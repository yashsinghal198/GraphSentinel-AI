import random
import pandas as pd
from faker import Faker

def generate_dataset(seed=42):
    """
    Generates synthetic customer data for the GraphSentinel AI system.
    Returns a pandas DataFrame containing 432 records.
    """
    Faker.seed(seed)
    random.seed(seed)
    fake = Faker()

    customers = []
    
    # 1. 380 independent, legitimate accounts
    for _ in range(380):
        customers.append({
            'customer_id': fake.uuid4(),
            'name': fake.name(),
            'email': fake.email(),
            'device_id': fake.uuid4(),
            'ip_subnet': fake.ipv4_private(network=False),
            'card_fingerprint': fake.credit_card_number(),
            'shipping_address': fake.address().replace('\n', ', '),
            'is_ring_member': False
        })
        
    # 2. 7 embedded abuse rings comprising 39 total accounts
    # Distributing 39 accounts across 7 rings
    ring_sizes = [6, 6, 6, 6, 5, 5, 5]
    for size in ring_sizes:
        # High weight signals shared among the ring
        shared_card = fake.credit_card_number()
        shared_device = fake.uuid4()
        
        for _ in range(size):
            customers.append({
                'customer_id': fake.uuid4(),
                'name': fake.name(),
                'email': fake.email(),
                # Ring members share device and card
                'device_id': shared_device, 
                'ip_subnet': fake.ipv4_private(network=False),
                'card_fingerprint': shared_card, 
                'shipping_address': fake.address().replace('\n', ', '),
                'is_ring_member': True
            })
            
    # 3. 5 "hard negative" groups comprising 15 total accounts
    # Innocent customers who share exactly one weak signal
    hn_sizes = [3, 3, 3, 3, 3]
    for size in hn_sizes:
        # Weak signal: either IP subnet or Shipping Address
        weak_signal_type = random.choice(['ip', 'address'])
        shared_ip = fake.ipv4_private(network=False)
        shared_address = fake.address().replace('\n', ', ')
        
        for _ in range(size):
            customers.append({
                'customer_id': fake.uuid4(),
                'name': fake.name(),
                'email': fake.email(),
                'device_id': fake.uuid4(),
                'ip_subnet': shared_ip if weak_signal_type == 'ip' else fake.ipv4_private(network=False),
                'card_fingerprint': fake.credit_card_number(),
                'shipping_address': shared_address if weak_signal_type == 'address' else fake.address().replace('\n', ', '),
                'is_ring_member': False # They are legitimate despite the weak signal overlap
            })
            
    # Shuffle the combined dataset
    random.shuffle(customers)
    
    # Return as pandas DataFrame
    df = pd.DataFrame(customers)
    return df

if __name__ == "__main__":
    print("Generating synthetic dataset...")
    df = generate_dataset()
    print(f"Total generated records: {len(df)}")
    
    is_ring = df['is_ring_member'] == True
    print(f"Independent legitimate accounts: {len(df[~is_ring]) - 15}") # Subtracting hard negatives
    print(f"Abuse ring accounts: {len(df[is_ring])}")
    print(f"Hard negative accounts: 15")
    
    # Save a copy for manual inspection if run directly
    df.to_csv("synthetic_customers.csv", index=False)
    print("Saved dataset to synthetic_customers.csv")
