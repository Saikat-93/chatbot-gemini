🐳 How to Run This Project Using Docker (Step-by-Step)
✅ Step 1: Install Docker

Make sure Docker is installed on your system.

👉 Check installation:

docker --version

If not installed:

Download from: https://www.docker.com/products/docker-desktop
📥 Step 2: Clone the Repository
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
⚙️ Step 3: Setup Environment Variables

Create a .env file in the root folder:

GEMINI_API_KEY=your_api_key_here

💡 (Use .env.example if provided)

🐳 Step 4: Build Docker Image
docker build -t chatbot-app .
▶️ Step 5: Run Docker Container
docker run -p 8000:8000 chatbot-app
🌐 Step 6: Access the Application

Open your browser:

👉 http://localhost:8000

👉 API Docs: http://localhost:8000/docs
