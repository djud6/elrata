# EAFC25 Player Price Tracker (2024)

![Project Banner](https://via.placeholder.com/800x200.png?text=EAFC25+Price+Tracker+-+Track+Market+Trends+in+Real-Time)  
*Automated pipeline to track player card price fluctuations in EAFC 25.*

---

## 📌 Overview
This project automates the collection and analysis of EAFC25 player card prices to identify market trends. By scraping data hourly, storing it in a cloud database, and visualizing results in Power BI, users can track price volatility and make data-driven decisions.

---

## 🚀 Features
- **Automated Web Scraping**: Python scripts collect player stats and prices hourly.
- **Price History Tracking**: SQL database records hourly fluctuations for 500+ player cards.
- **Scalable Cloud Architecture**: AWS RDS handles 10,000+ hourly entries with optimized query performance.
- **GitHub Actions Automation**: Scheduled YAML workflows run scraping scripts without manual intervention.
- **Interactive Dashboards**: Power BI visualizes price trends, top-valued cards, and volatility patterns.

---

## 🛠️ Technologies Used
- **Python**: Core scripting for scraping and data processing.
- **AWS RDS**: MySQL database for structured, scalable storage.
- **GitHub Actions**: CI/CD pipeline for hourly script execution.
- **Power BI**: Interactive dashboards for data visualization.
- **Beautiful Soup/Requests**: Web scraping libraries.
- **SQLAlchemy**: Database ORM for Python-to-SQL integration.
