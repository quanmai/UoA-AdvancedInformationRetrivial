#!/bin/bash

while getopts ":d:q:" opt; do
  case $opt in
    d)
      words=$OPTARG
      ;;
    q)
      output_dir=$OPTARG
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      ;;
  esac
done

# Call the Python script with the provided arguments
python query.py -d "$words" -q "$output_dir"
