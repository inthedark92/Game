import React, { useEffect, useState } from 'react';
import axios from 'axios';

interface InventoryItem {
    id: number;
    item: {
        name: string;
        image: string;
        description: string;
    };
    quantity: number;
    is_equipped: boolean;
}

const InventoryPanel: React.FC = () => {
    const [items, setItems] = useState<InventoryItem[]>([]);

    useEffect(() => {
        fetchInventory();
    }, []);

    const fetchInventory = async () => {
        try {
            const response = await axios.get('/api/v2/inventory/');
            setItems(response.data);
        } catch (error) {
            console.error('Error fetching inventory:', error);
        }
    };

    const equipItem = async (id: number) => {
        await axios.post('/api/v2/inventory/equip/', { item_id: id });
        fetchInventory();
    };

    return (
        <div className="inventory-panel" style={{ display: 'grid', gridTemplateColumns: 'repeat(8, 1fr)', gap: '5px' }}>
            {items.map(item => (
                <div key={item.id} className="inventory-slot" style={{
                    border: '1px solid #444',
                    padding: '5px',
                    background: item.is_equipped ? '#442' : '#222',
                    cursor: 'pointer'
                }} onClick={() => !item.is_equipped && equipItem(item.id)}>
                    <img src={item.item.image || '/static/img/default_item.png'} alt={item.item.name} style={{ width: '100%' }} />
                    <div style={{ fontSize: '10px', textAlign: 'center' }}>x{item.quantity}</div>
                </div>
            ))}
        </div>
    );
};

export default InventoryPanel;
