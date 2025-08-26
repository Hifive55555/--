import os
from classifier import train, save

def load_dataset(pos_file, neg_file):
    """Load positive and negative samples from files"""
    news_data = []
    labels = []
    
    # Load positive samples
    try:
        with open(pos_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():  # Skip empty lines
                    news_data.append(line.strip())
                    labels.append(1)
    except FileNotFoundError:
        print(f"Warning: Could not find positive samples file: {pos_file}")
    
    # Load negative samples
    try:
        with open(neg_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():  # Skip empty lines
                    news_data.append(line.strip())
                    labels.append(0)
    except FileNotFoundError:
        print(f"Warning: Could not find negative samples file: {neg_file}")
    
    return news_data, labels

def process_folder(folder_path):
    """Process a single training folder"""
    pos_file = os.path.join(folder_path, "a.txt")
    neg_file = os.path.join(folder_path, "b.txt")
    weight_file = os.path.join(folder_path, "weight.json")
    
    # Load datasets
    print(f"\nProcessing folder: {folder_path}")
    news_data, labels = load_dataset(pos_file, neg_file)
    
    if not news_data:
        print("Error: No training data loaded in this folder!")
        return
    
    # Train the classifier
    print("Training classifier...")
    training_result = train(news_data, labels)
    
    # Save the weights
    print("Saving weights...")
    save(training_result, weight_file)
    
    print(f"Training completed! Weights saved to {weight_file}")
    print(f"Total samples processed: {len(news_data)}")
    print(f"Positive samples: {training_result['positive_data']}")
    print(f"Negative samples: {training_result['nagetive_data']}")

def start_training() -> str:
    """Start training process and return result message"""
    try:
        # Define base folder
        set_folder = "train_set"
        
        # Get all subfolders
        try:
            subfolders = [f.path for f in os.scandir(set_folder) if f.is_dir()]
        except FileNotFoundError:
            return f"错误：未找到训练集文件夹: {set_folder}"
        
        if not subfolders:
            return "错误：训练集文件夹中没有子文件夹！"
        
        # Process each subfolder
        results = []
        for folder in subfolders:
            folder_name = os.path.basename(folder)
            pos_file = os.path.join(folder, "a.txt")
            neg_file = os.path.join(folder, "b.txt")
            weight_file = os.path.join(folder, "weight.json")
            
            # Load datasets
            news_data, labels = load_dataset(pos_file, neg_file)
            
            if not news_data:
                results.append(f"[{folder_name}] 错误：无训练数据")
                continue
            
            # Train the classifier
            training_result = train(news_data, labels)
            
            # Save the weights
            save(training_result, weight_file)
            
            results.append(
                f"[{folder_name}] 完成：共 {len(news_data)} 样本"
                f"（正面 {training_result['positive_data']}，"
                f"负面 {training_result['nagetive_data']}）"
            )
        
        return "\n".join(results)
        
    except Exception as e:
        return f"训练过程出错：{str(e)}"

if __name__ == "__main__":
    print(start_training())