#! /bin/bash
source activate VQC
conda info --env
conda list
python --version

python vsfa_train.py main --model-name=VSFA \
                          --database=KoNViD \
                          --feature_folder=/home/kedeleshier/lzq/VQAFeatures/VSFA/KoNViD \
                          --database_info_path=data/KoNViD_1k/KoNViD_1k.csv \
                          --split_idx_file_path='["data/KoNViD_1k/train_val_test_split.xlsx","data/KoNViD_1k/train_val_test_split_1.xlsx","data/KoNViD_1k/train_val_test_split_2.xlsx","data/KoNViD_1k/train_val_test_split_3.xlsx","data/KoNViD_1k/train_val_test_split_4.xlsx","data/KoNViD_1k/train_val_test_split_5.xlsx","data/KoNViD_1k/train_val_test_split_6.xlsx","data/KoNViD_1k/train_val_test_split_7.xlsx","data/KoNViD_1k/train_val_test_split_8.xlsx","data/KoNViD_1k/train_val_test_split_9.xlsx"]' \
                          --train_feature_shuffle=False \
                          --val_feature_shuffle=False \
                          --test_feature_shuffle=False \
                          --num_epochs=2000 \
                          --feature_dim=4096 \
                          --train_batchsize=16

python vsfa_train.py main --model-name=VSFA \
                          --database=KoNViD \
                          --feature_folder=/home/kedeleshier/lzq/VQAFeatures/VSFA/KoNViD \
                          --database_info_path=data/KoNViD_1k/KoNViD_1k.csv \
                          --split_idx_file_path='["data/KoNViD_1k/train_val_test_split.xlsx","data/KoNViD_1k/train_val_test_split_1.xlsx","data/KoNViD_1k/train_val_test_split_2.xlsx","data/KoNViD_1k/train_val_test_split_3.xlsx","data/KoNViD_1k/train_val_test_split_4.xlsx","data/KoNViD_1k/train_val_test_split_5.xlsx","data/KoNViD_1k/train_val_test_split_6.xlsx","data/KoNViD_1k/train_val_test_split_7.xlsx","data/KoNViD_1k/train_val_test_split_8.xlsx","data/KoNViD_1k/train_val_test_split_9.xlsx"]' \
                          --train_feature_shuffle=False \
                          --val_feature_shuffle=False \
                          --test_feature_shuffle=True \
                          --num_epochs=2000 \
                          --feature_dim=4096 \
                          --train_batchsize=16

python vsfa_train.py main --model-name=VSFA \
                          --database=KoNViD \
                          --feature_folder=/home/kedeleshier/lzq/VQAFeatures/VSFA/KoNViD \
                          --database_info_path=data/KoNViD_1k/KoNViD_1k.csv \
                          --split_idx_file_path='["data/KoNViD_1k/train_val_test_split.xlsx","data/KoNViD_1k/train_val_test_split_1.xlsx","data/KoNViD_1k/train_val_test_split_2.xlsx","data/KoNViD_1k/train_val_test_split_3.xlsx","data/KoNViD_1k/train_val_test_split_4.xlsx","data/KoNViD_1k/train_val_test_split_5.xlsx","data/KoNViD_1k/train_val_test_split_6.xlsx","data/KoNViD_1k/train_val_test_split_7.xlsx","data/KoNViD_1k/train_val_test_split_8.xlsx","data/KoNViD_1k/train_val_test_split_9.xlsx"]' \
                          --train_feature_shuffle=True \
                          --val_feature_shuffle=True \
                          --test_feature_shuffle=False \
                          --num_epochs=2000 \
                          --feature_dim=4096 \
                          --train_batchsize=16

python vsfa_train.py main --model-name=VSFA \
                          --database=KoNViD \
                          --feature_folder=/home/kedeleshier/lzq/VQAFeatures/VSFA/KoNViD \
                          --database_info_path=data/KoNViD_1k/KoNViD_1k.csv \
                          --split_idx_file_path='["data/KoNViD_1k/train_val_test_split.xlsx","data/KoNViD_1k/train_val_test_split_1.xlsx","data/KoNViD_1k/train_val_test_split_2.xlsx","data/KoNViD_1k/train_val_test_split_3.xlsx","data/KoNViD_1k/train_val_test_split_4.xlsx","data/KoNViD_1k/train_val_test_split_5.xlsx","data/KoNViD_1k/train_val_test_split_6.xlsx","data/KoNViD_1k/train_val_test_split_7.xlsx","data/KoNViD_1k/train_val_test_split_8.xlsx","data/KoNViD_1k/train_val_test_split_9.xlsx"]' \
                          --train_feature_shuffle=True \
                          --val_feature_shuffle=True \
                          --test_feature_shuffle=True \
                          --num_epochs=2000 \
                          --feature_dim=4096 \
                          --train_batchsize=16
