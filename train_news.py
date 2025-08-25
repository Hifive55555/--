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

def main():
    # Define file paths
    pos_file = "train_set/news.pos.txt"
    neg_file = "train_set/news.neg.txt"
    weight_file = "news.weight.json"
    
    # Load datasets
    print("Loading datasets...")
    news_data, labels = load_dataset(pos_file, neg_file)
    
    if not news_data:
        print("Error: No training data loaded!")
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

if __name__ == "__main__":
    main()