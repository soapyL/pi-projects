const express = require("express");
const http = require("http");
const socketIo = require("socket.io");
const ffmpeg = require("fluent-ffmpeg");
const cors = require("cors");
const fs = require("fs");
const path = require("path");

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
	cors: {
		origin: "*",
	},
});

const MJPEG_STREAM_URL = "http://<RPI_IP>:8080/?action=stream";
let isRecording = false;
let ffmpegProcess = null;

app.use(cors());
app.use(express.json());
app.use(express.static("recordings"));

app.get("/stream", (req, res) => {
	res.json({ url: MJPEG_STREAM_URL });
});

io.on("connection", (socket) => {
	console.log("Client connected");

	socket.on("start-recording", () => {
		if (isRecording) return;
		isRecording = true;

		const fileName = `recordings/stream-${Date.now()}.mp4`;
		ffmpegProcess = ffmpeg(MJPEG_STREAM_URL)
		.inputFormat("mjpeg")
		.save(fileName)
		.on("end", () => {
			console.log(`Recording saved: ${fileName}`);
		})
		.on("error", (err) => {
			console.error("FFmpeg error:", err);
		});

		socket.emit("recording-started", { fileName });
	});

	socket.on("stop-recording", () => {
		if (!isRecording || !ffmpegProcess) return;
		ffmpegProcess.kill("SIGINT");
		isRecording = false;
		socket.emit("recording-stopped");
	});

	socket.on("disconnect", () => {
		console.log("Client disconnected");
	});
});

const PORT = 8000;
server.listen(PORT, () => {
	console.log(`Server running on http://localhost:${PORT}`);
});
