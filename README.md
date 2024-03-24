# auto-transcode
Automated remux and transcode videos recorded by [Mikufans BililiveRecorder](https://github.com/BililiveRecorder/BililiveRecorder)

## What it does

1. Watches the recorder save directories

1. Remux .flv files into .mp4 format

1. Rename the recorded video files and danmaku files

1. Transcode the video files with storage settings (av1 encoding) and move to storage folder

## Setup

### Environment

```sh
conda create -n auto-transcode python=3.11 -y
conda activate auto-transcode
```

### Pre-commit

## Run
