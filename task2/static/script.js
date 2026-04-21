const form = document.getElementById("audioForm");
const sourceAudioInput = document.getElementById("sourceAudioInput");
const senderPortInput = document.getElementById("senderPortInput");
const receiverPortInput = document.getElementById("receiverPortInput");
const checkBtn = document.getElementById("checkBtn");
const errorBox = document.getElementById("errorBox");
const resultBox = document.getElementById("resultBox");
const tableBox = document.getElementById("tableBox");
const resultTableBody = document.getElementById("resultTableBody");

const resSourceFilename = document.getElementById("resSourceFilename");
const resSourceSize = document.getElementById("resSourceSize");
const resMaxSafe = document.getElementById("resMaxSafe");
const resClass = document.getElementById("resClass");
const resPacket = document.getElementById("resPacket");
const resStatus = document.getElementById("resStatus");
const resPercent = document.getElementById("resPercent");
const meterFill = document.getElementById("meterFill");
const resSourceHash = document.getElementById("resSourceHash");

function showError(message) {
    errorBox.textContent = message;
    errorBox.classList.remove("hidden");
}

function hideError() {
    errorBox.classList.add("hidden");
    errorBox.textContent = "";
}

function renderPacketRows(packetResults) {
    resultTableBody.innerHTML = "";

    for (const row of packetResults) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${row.packet_size}</td>
            <td>${row.sender_port}</td>
            <td>${row.receiver_port}</td>
            <td>${Number(row.similarity_percent).toFixed(4)}</td>
            <td>${row.exact_match ? "Yes" : "No"}</td>
            <td>${row.quality}</td>
            <td>${row.safe_for_transfer ? "Yes" : "No"}</td>
            <td>${Number(row.duration_ms).toFixed(2)}</td>
        `;

        if (row.error) {
            tr.classList.add("row-error");
            tr.title = row.error;
        }

        resultTableBody.appendChild(tr);
    }
}

function showResult(data) {
    const isSafe = data.max_safe_transmit_mb > 0;

    resultBox.classList.remove("hidden", "ok", "fail");
    resultBox.classList.add(isSafe ? "ok" : "fail");
    tableBox.classList.remove("hidden");

    resSourceFilename.textContent = data.source_filename;
    resSourceSize.textContent = Number(data.source_size_mb).toFixed(2);
    resMaxSafe.textContent = Number(data.max_safe_transmit_mb).toFixed(2);
    resClass.textContent = data.transfer_class;
    resPacket.textContent = data.recommended_packet_size ? `${data.recommended_packet_size} bytes` : "None";
    resStatus.textContent = data.safety_message;
    resSourceHash.textContent = data.source_hash;

    const safePercent = data.max_safe_transmit_mb;
    const visualPercent = Math.min(safePercent, 100);
    meterFill.style.width = `${visualPercent}%`;
    meterFill.classList.toggle("over", !isSafe);
    resPercent.textContent = safePercent.toFixed(2);

    renderPacketRows(data.packet_results || []);
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    hideError();

    if (!sourceAudioInput.files.length) {
        showError("Please upload a source audio file.");
        return;
    }

    const formData = new FormData();
    formData.append("source_audio", sourceAudioInput.files[0]);
    formData.append("sender_port", senderPortInput.value);
    formData.append("receiver_port", receiverPortInput.value);

    checkBtn.disabled = true;
    checkBtn.textContent = "Running...";

    try {
        const response = await fetch("/api/run-transfer", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            showError(data.error || "Unable to run transfer test.");
            return;
        }

        showResult(data);
    } catch (error) {
        showError(`Unexpected error: ${error.message}`);
    } finally {
        checkBtn.disabled = false;
        checkBtn.textContent = "Run Transfer Test";
    }
});
