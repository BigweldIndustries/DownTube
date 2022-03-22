<img src="title.png" width="800">
A simple GUI wrapper for yt-dlp that allows you to easily archive youtube channels. Completely free and open source.

## Who is this for?
I am sure you are at least somewhat familiar with the idea of internet archivists, or people who archive content in case of a takedown or some other reason. This tool is for people who want to back up their favorite channels, but do not know how to program or use complicated command line tools

## How to install?
First install [python](https://python.org/downloads)

1. Download the folder from this page
2. Extract it

#### Windows:
3. Double click on the RunWindows.bat and it does all of the work for you

#### Linux:
3. Open terminal in app folder
4. run `chmod +x RunLinux.sh` (If fails, run with sudo)
5. Either double click on RunLinux.sh or just run it via `./RunLinux.sh`

## Tips
This uses yt-dlp, so if you are archiving more than 5 channels at a time, this may cause throttling. I will fix this in a future update by queing channels 5 at a time.

## Todo:
* [x] Live logging
* [x] Save last path
* [x] Auto load archive.txt
* [ ] Queueing system
* [X] Errors tab
* [X] Individual tabs for each archival thread
