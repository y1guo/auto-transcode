# auto-transcode

Automated remux and transcode videos recorded by [Mikufans BililiveRecorder](https://github.com/BililiveRecorder/BililiveRecorder)

## What it does

1. Watches the recorder save directories

1. Remux .flv files into .mp4 format

1. Rename the recorded video files and danmaku files

1. Transcode the video files with storage settings (av1 encoding) and move to storage folder

## Setup

### Environment

Install python environment with the following

```sh
conda create -n auto-transcode python=3.11 -y
conda activate auto-transcode
conda install -c conda-forge ffmpeg -y
pip install -r requirements.txt
```

### env

Create a `.env` file

```sh
cp .env.example .env
```

Then configure the environment variables in `.env`

### Pre-commit

```sh
pip install pre-commit
pre-commit install
```

## Run

```sh
uvicorn auto-transcode.main:app
```

### Note

You must set the `Recording File Name Formatting` in Mikufans BililiveRecorder as

```
{{ roomId }}-{{ name }}/{{ roomId }}_{{ "now" | format_date: "yyyyMMdd_HHmmss" }}_{{ title }}.flv
```

in order for auto-transcode to correctly recognize the recording files and rename them.
