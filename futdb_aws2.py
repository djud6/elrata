import mysql.connector
from bs4 import BeautifulSoup
import requests
import pandas as pd
import time
from datetime import datetime

def clean_price(price_str):
    """Convert price string (e.g., '480K') to integer value"""
    if not price_str or price_str == 'N/A':
        return None
    price_str = price_str.strip().upper()
    multiplier = 1
    if 'K' in price_str:
        multiplier = 1000
        price_str = price_str.replace('K', '')
    elif 'M' in price_str:
        multiplier = 1000000
        price_str = price_str.replace('M', '')
    try:
        return int(float(price_str) * multiplier)
    except:
        return None

def clean_stat(stat_str):
    """Convert stat string to integer, handling N/A cases"""
    if not stat_str or stat_str == 'N/A':
        return None
    try:
        return int(stat_str)
    except:
        return None

def create_database():
    """Create the necessary database tables if they don't exist"""

    # Updated connection configuration
    conn = mysql.connector.connect(
        host="fut-db.c3q8kcygm89u.us-east-2.rds.amazonaws.com",
        user="admin",
        password="Dave&busters11",
        database="fut_db",
        port=3306
    )

    c = conn.cursor()
    
    # Create players table
    c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            player_id INT NOT NULL AUTO_INCREMENT,
            name VARCHAR(255),
            rating INT,
            position VARCHAR(10),
            image_url VARCHAR(255),
            pace INT,
            shooting INT,
            passing INT,
            dribbling INT,
            defending INT,
            physical INT,
            skills_weakfoot VARCHAR(10),
            foot VARCHAR(10),
            last_updated DATETIME,
            PRIMARY KEY (player_id)
        )
    ''')
    
    # Create price history table with unique constraint
    c.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            price_id INT NOT NULL AUTO_INCREMENT,
            player_id INT,
            price INT,
            timestamp DATETIME,
            PRIMARY KEY (price_id),
            FOREIGN KEY (player_id) REFERENCES players(player_id),
            UNIQUE KEY unique_price_entry (player_id, timestamp)
        )
    ''')
    
    conn.commit()
    conn.close()

def scrape_and_update_database(min_rating=80, min_price=1000, max_price=6000000, max_pages=50):
    base_url = "https://www.futwiz.com/en/fc25/players"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US, en;q=0.5'
    }
    
    conn = mysql.connector.connect(
        host="fut-db.c3q8kcygm89u.us-east-2.rds.amazonaws.com",
        user="admin",
        password="Dave&busters11",
        database="fut_db",
        port=3306
    )
    c = conn.cursor(buffered=True)
    current_time = datetime.now()
    
    for page in range(max_pages):
        try:
            params = {
                'page': page,
                'minrating': min_rating,
                'minprice': min_price,
                'maxprice': max_price
            }
            
            time.sleep(2)  # Respect rate limiting
            webpage = requests.get(base_url, params=params, headers=headers)
            webpage.raise_for_status()
            
            soup = BeautifulSoup(webpage.content, "html.parser")
            players = soup.find_all('div', class_='player-search-result-row')
            
            if not players:
                print(f"No more players found after page {page}")
                break
            
            for player in players:
                # Extract player data
                name = player.find('div', class_='player-name').find('b').text.strip()
                rating_div = player.find('div', class_='otherversion24-txt')
                rating = clean_stat(rating_div.text.strip() if rating_div else 'N/A')
                position = player.find('div', class_='mainpos').text.strip()
                image_url = player.find('div', class_='face').find('img', class_='player-img')['src']
                
                # Get stats
                stats_blocks = player.find_all('div', class_='search-stats-block')
                stats = {}
                for block in stats_blocks:
                    stat_name = block.find('div', class_='search-block-header').text.strip()
                    stat_value = block.find('div', class_='search-block-data').text.strip()
                    stats[stat_name] = stat_value
                
                # Get current price
                price_div = player.find('div', class_='price')
                price = clean_price(price_div.text.strip() if price_div else 'N/A')
                
                # Check if this specific version of the player exists
                c.execute('''
                    SELECT player_id, last_updated 
                    FROM players 
                    WHERE name = %s AND rating = %s AND position = %s
                ''', (name, rating, position))
                result = c.fetchone()
                
                if result:
                    # Update existing player
                    player_id = result[0]
                    last_updated = result[1]
                    
                    # Only update if the current price is different from the last recorded price
                    if price is not None:
                        c.execute('''
                            SELECT price 
                            FROM price_history 
                            WHERE player_id = %s 
                            ORDER BY timestamp DESC 
                            LIMIT 1
                        ''', (player_id,))
                        last_price = c.fetchone()
                        
                        if not last_price or last_price[0] != price:
                            try:
                                c.execute('''
                                    INSERT INTO price_history (player_id, price, timestamp)
                                    VALUES (%s, %s, %s)
                                ''', (player_id, price, current_time))
                            except mysql.connector.IntegrityError:
                                # Skip if we already have a price for this timestamp
                                pass
                    
                    # Update player stats
                    c.execute('''
                        UPDATE players 
                        SET image_url = %s, pace = %s, shooting = %s, 
                            passing = %s, dribbling = %s, defending = %s, physical = %s,
                            skills_weakfoot = %s, foot = %s, last_updated = %s
                        WHERE player_id = %s
                    ''', (
                        image_url,
                        clean_stat(stats.get('PAC')), clean_stat(stats.get('SHO')),
                        clean_stat(stats.get('PAS')), clean_stat(stats.get('DRI')),
                        clean_stat(stats.get('DEF')), clean_stat(stats.get('PHY')),
                        stats.get('SM/WF'), stats.get('Foot'),
                        current_time, player_id
                    ))
                else:
                    # Insert new player
                    c.execute('''
                        INSERT INTO players (
                            name, rating, position, image_url, pace, shooting,
                            passing, dribbling, defending, physical,
                            skills_weakfoot, foot, last_updated
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        name, rating, position, image_url,
                        clean_stat(stats.get('PAC')), clean_stat(stats.get('SHO')),
                        clean_stat(stats.get('PAS')), clean_stat(stats.get('DRI')),
                        clean_stat(stats.get('DEF')), clean_stat(stats.get('PHY')),
                        stats.get('SM/WF'), stats.get('Foot'),
                        current_time
                    ))
                    player_id = c.lastrowid
                    
                    # Add initial price record
                    if price is not None:
                        c.execute('''
                            INSERT INTO price_history (player_id, price, timestamp)
                            VALUES (%s, %s, %s)
                        ''', (player_id, price, current_time))
            
            print(f"Scraped page {page} successfully")
            conn.commit()
            
        except Exception as e:
            print(f"Error on page {page}: {str(e)}")
            continue
    
    conn.close()


if __name__ == "__main__":
    # Create database tables
    create_database()
    
    # Run the scraper
    scrape_and_update_database(
        min_rating=86,
        min_price=0,
        max_price=50000000,
        max_pages=50
    )

