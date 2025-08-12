# Ente Sync Tool

This document describes how to use the `ente-sync` tool to synchronize a photo library from an Ente account to a local on-disk library, and then ingest the missing photos into Immich.

## Overview

The `ente-sync` tool is designed to be a generic and efficient way to synchronize photos between different libraries. It works in two phases:

1.  **Analysis Phase:** The tool compares a source library (Ente) with a destination library (a local on-disk directory, which should be your Immich library) to identify which photos are missing from the destination. This comparison is done using BLAKE2b hashes, which is very efficient and avoids downloading all the files.

2.  **Ingestion Phase:** The tool takes the list of missing photos and ingests them into a target service. In this case, the target service is Immich, and the ingestion is done by uploading the photos using the Immich API.

This two-phase design makes the tool very flexible. In the future, it could be extended to support other source libraries and other ingestion methods (e.g., downloading to a local directory).

## Prerequisites

1.  **`ente-tools` Installed:** You must have the `ente-tools` package installed.
2.  **Linked Ente Account:** You must have already linked your Ente account using the main `ente-tool` CLI. If you haven't done this, run the following command and follow the prompts:
    ```bash
    ente-tool link <your-ente-email>
    ```
3.  **On-disk Immich Library:** The tool needs access to the on-disk Immich library. You should run this tool on the same server where your Immich library is stored.

## Usage

The script is run from the command line using the `ente-sync` command.

```bash
ente-sync [OPTIONS]
```

### Options

*   `--ente-email TEXT`: Your Ente email address. **(Required)**
*   `--immich-lib-dir PATH`: The path to your on-disk Immich library. **(Required)**
*   `--immich-url TEXT`: The URL of your Immich server. **(Required)**
*   `--immich-api-key TEXT`: Your Immich API key. **(Required)**

### Example

```bash
ente-sync \
    --ente-email "user@example.com" \
    --immich-lib-dir "/path/to/your/immich/library" \
    --immich-url "http://immich.example.com:2283" \
    --immich-api-key "your_long_api_key_here"
```

The script will first scan your local Immich library and your Ente library to find the missing photos. Then, it will display a progress bar as it ingests the missing photos into Immich.
