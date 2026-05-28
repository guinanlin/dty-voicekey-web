#!/bin/bash

bun --bun run dev &

bun watcher.js

wait
