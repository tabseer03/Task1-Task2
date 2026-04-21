from pathlib import Path
import hashlib
import socket
import threading
import time
from flask import Flask, jsonify, render_template, request

app = Flask(__name__, template_folder="templates", static_folder="static")

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

MAX_UPLOAD_MB = 100
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
PACKET_SIZES = [8, 16, 32, 64]
SAFE_SIMILARITY_THRESHOLD = 99.0

ALLOWED_EXTENSIONS = {
	"mp3",
	"wav",
	"aac",
	"m4a",
	"ogg",
	"flac",
	"wma",
	"amr",
	"opus",
}

app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES


def is_allowed_file(filename: str) -> bool:
	return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def classify_capacity(size_mb: float) -> str:
	if size_mb <= 0:
		return "Not Safe"
	if size_mb < 5:
		return "Small Payload"
	if size_mb < 20:
		return "Medium Payload"
	if size_mb < 50:
		return "Large Payload"
	return "Very Large Payload"


def classify_packet_quality(exact_match: bool, similarity_percent: float) -> str:
	if exact_match:
		return "Excellent"
	if similarity_percent >= 99.9:
		return "Very Good"
	if similarity_percent >= SAFE_SIMILARITY_THRESHOLD:
		return "Good (Minor Errors Tolerated)"
	if similarity_percent >= 95:
		return "Fair"
	return "Poor"


def calculate_similarity_percent(source_bytes: bytes, received_bytes: bytes) -> float:
	max_len = max(len(source_bytes), len(received_bytes))
	if max_len == 0:
		return 100.0

	min_len = min(len(source_bytes), len(received_bytes))
	matching = 0
	for idx in range(min_len):
		if source_bytes[idx] == received_bytes[idx]:
			matching += 1

	return (matching / max_len) * 100


def transfer_over_tcp(source_bytes: bytes, packet_size: int, sender_port: int, receiver_port: int):
	received_chunks = []
	errors = []
	server_ready = threading.Event()

	def receiver_worker():
		try:
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as receiver:
				receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				receiver.bind(("127.0.0.1", receiver_port))
				receiver.listen(1)
				receiver.settimeout(5)
				server_ready.set()

				connection, _ = receiver.accept()
				with connection:
					connection.settimeout(5)
					while True:
						chunk = connection.recv(packet_size)
						if not chunk:
							break
						received_chunks.append(chunk)
		except Exception as exc:
			errors.append(str(exc))
			server_ready.set()

	receiver_thread = threading.Thread(target=receiver_worker, daemon=True)
	receiver_thread.start()

	if not server_ready.wait(timeout=2):
		raise RuntimeError("Receiver port did not initialize in time.")

	time.sleep(0.05)
	start = time.perf_counter()
	try:
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sender:
			sender.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			sender.bind(("127.0.0.1", sender_port))
			sender.connect(("127.0.0.1", receiver_port))
			for idx in range(0, len(source_bytes), packet_size):
				sender.sendall(source_bytes[idx : idx + packet_size])
	finally:
		receiver_thread.join(timeout=5)

	duration_ms = (time.perf_counter() - start) * 1000

	if errors:
		raise RuntimeError(errors[0])

	if receiver_thread.is_alive():
		raise RuntimeError("Receiver timed out before completing transfer.")

	return b"".join(received_chunks), duration_ms


@app.route("/")
def index():
	return render_template("index.html")


@app.route("/api/run-transfer", methods=["POST"])
def run_transfer_test():
	if "source_audio" not in request.files:
		return jsonify({"success": False, "error": "Upload a source audio file."}), 400

	source_audio = request.files["source_audio"]

	if source_audio.filename == "":
		return jsonify({"success": False, "error": "Source file is required."}), 400

	if not is_allowed_file(source_audio.filename):
		return jsonify(
			{
				"success": False,
				"error": "Unsupported format. Use MP3, WAV, AAC, M4A, OGG, FLAC, WMA, AMR, or OPUS.",
			}
		), 400

	source_bytes = source_audio.read()
	if not source_bytes:
		return jsonify({"success": False, "error": "Source audio file is empty."}), 400

	try:
		sender_base_port = int(request.form.get("sender_port", 6100))
		receiver_base_port = int(request.form.get("receiver_port", 6200))
	except ValueError:
		return jsonify({"success": False, "error": "Ports must be numeric values."}), 400

	if not (1024 <= sender_base_port <= 65000 and 1024 <= receiver_base_port <= 65000):
		return jsonify({"success": False, "error": "Use ports in range 1024 to 65000."}), 400

	source_size_mb = len(source_bytes) / (1024 * 1024)
	source_hash = hashlib.sha256(source_bytes).hexdigest()

	packet_results = []
	safe_packet_candidates = []

	for index, packet_size in enumerate(PACKET_SIZES):
		sender_port = sender_base_port + index
		receiver_port = receiver_base_port + index

		if sender_port == receiver_port:
			receiver_port += 100

		try:
			reconstructed_bytes, duration_ms = transfer_over_tcp(
				source_bytes=source_bytes,
				packet_size=packet_size,
				sender_port=sender_port,
				receiver_port=receiver_port,
			)

			reconstructed_hash = hashlib.sha256(reconstructed_bytes).hexdigest()
			exact_match = reconstructed_hash == source_hash
			similarity = calculate_similarity_percent(source_bytes, reconstructed_bytes)
			safe_for_transfer = similarity >= SAFE_SIMILARITY_THRESHOLD
			quality = classify_packet_quality(exact_match, similarity)
			throughput_mbps = (source_size_mb / (duration_ms / 1000)) if duration_ms > 0 else 0.0

			packet_results.append(
				{
					"packet_size": packet_size,
					"sender_port": sender_port,
					"receiver_port": receiver_port,
					"received_size_mb": round(len(reconstructed_bytes) / (1024 * 1024), 4),
					"exact_match": exact_match,
					"similarity_percent": round(similarity, 4),
					"safe_for_transfer": safe_for_transfer,
					"quality": quality,
					"duration_ms": round(duration_ms, 2),
					"throughput_mbps": round(throughput_mbps, 4),
				}
			)

			if safe_for_transfer:
				safe_packet_candidates.append((similarity, throughput_mbps, packet_size))
		except Exception as exc:
			packet_results.append(
				{
					"packet_size": packet_size,
					"sender_port": sender_port,
					"receiver_port": receiver_port,
					"exact_match": False,
					"similarity_percent": 0,
					"safe_for_transfer": False,
					"quality": "Error",
					"duration_ms": 0,
					"throughput_mbps": 0,
					"error": str(exc),
				}
			)

	if safe_packet_candidates:
		best_similarity, _, best_packet_size = max(safe_packet_candidates)
		max_safe_transfer_mb = round(source_size_mb, 2)
		transfer_class = classify_capacity(max_safe_transfer_mb)
		safety_message = (
			f"Safe transfer verified. Recommended packet size is {best_packet_size} bytes "
			f"(similarity {best_similarity:.4f}%)."
		)
	else:
		best_packet_size = None
		max_safe_transfer_mb = 0
		transfer_class = "Not Safe"
		safety_message = "No packet size met safe transfer threshold."

	return jsonify(
		{
			"success": True,
			"source_filename": source_audio.filename,
			"source_size_mb": round(source_size_mb, 2),
			"source_hash": source_hash,
			"max_safe_transmit_mb": max_safe_transfer_mb,
			"transfer_class": transfer_class,
			"recommended_packet_size": best_packet_size,
			"safe_similarity_threshold": SAFE_SIMILARITY_THRESHOLD,
			"packet_results": packet_results,
			"safety_message": safety_message,
		}
	)


@app.errorhandler(413)
def payload_too_large(_error):
	return (
		jsonify(
			{
				"success": False,
				"error": f"File too large. Max upload size is {MAX_UPLOAD_MB}MB.",
			}
		),
		413,
	)


if __name__ == "__main__":
	app.run(debug=True, host="localhost", port=5001)