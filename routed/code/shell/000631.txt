#!/usr/bin/env bash

inputDir=colorOut
outputDir=testOut
numPartitions=15
mapMovie=colorMap
transformMovie=colorTransform

hadoop fs -rm -skipTrash $outputDir/*
rm map/*
rm transform/*

PYSPARK_PYTHON=/opt/miniconda3/envs/pyspark/bin/python \
   spark-submit \
   --conf spark.yarn.appMasterEnv.PYSPARK_PYTHON=/opt/miniconda3/envs/pyspark/bin/python \
   --master yarn-cluster \
   --executor-memory 6G \
   --num-executors 15 \
   --executor-cores 11 \
   --driver-memory 6G \
   --files /home/brad/brad.keytab \
   color.py \
   $inputDir \
   $outputDir \
   $numPartitions

hadoop fs -get $outputDir/M* map
hadoop fs -get $outputDir/T* transform

rm $mapMovie.mp4
rm $transformMovie.mp4
cat map/*.png | ffmpeg -f image2pipe -r 10 -i - -c:v libx264 -pix_fmt yuv420p $mapMovie.mp4
cat transform/*.png | ffmpeg -f image2pipe -r 10 -i - -c:v libx264 -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" $transformMovie.mp4