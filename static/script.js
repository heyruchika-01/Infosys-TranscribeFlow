let mediaRecorder;
let audioChunks = [];
let audioStream = null;

// Start Recording

async function startRecording() {
    try {
        // Ask microphone permission
        audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });

        mediaRecorder = new MediaRecorder(audioStream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.start();

        const status = document.getElementById("recordStatus");
        if (status) status.innerText = "Recording... 🎙";

    } catch (error) {
        alert("Microphone access denied or not supported in this browser.");
        console.error("Mic error:", error);
    }
}


// Stop Recording & Send to Flask

function stopRecording() {

    if (!mediaRecorder) {
        alert("Recording has not started yet.");
        return;
    }

    mediaRecorder.stop();

    mediaRecorder.onstop = async () => {

        const status = document.getElementById("recordStatus");
        if (status) status.innerText = "Processing... ⏳";

        // Stop microphone stream
        if (audioStream) {
            audioStream.getTracks().forEach(track => track.stop());
        }

        // Create audio blob
        const audioBlob = new Blob(audioChunks, { type: "audio/wav" });

        // Create form data
        const formData = new FormData();
        formData.append("audio_file", audioBlob, "live_record.wav");

        try {
            const response = await fetch("/upload-audio", {
                method: "POST",
                body: formData
            });

            console.log("Response status:", response.status);

            if (!response.ok) {
                throw new Error("Server error while uploading audio.");
            }

            const html = await response.text();

            // Replace entire page with new rendered page
            document.open();
            document.write(html);
            document.close();

        } catch (error) {
            alert("Error while sending audio to server.");
            console.error("Upload error:", error);

            if (status) status.innerText = "Error occurred ❌";
        }
    };
}
