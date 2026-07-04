#!/bin/bash

bun --bun run dev -- -p 3600 &

bun watcher.js

wait
