# cs532-final-project
Scalable ML inference system with batching, scheduling, and worker-based execution.

# ML Inference Serving System

This project implements a scalable machine learning inference system designed to handle incoming prediction requests efficiently under varying workloads.

The system focuses on **systems design for ML inference**, including batching, scheduling, and concurrent request handling, rather than model training or accuracy.

## 🚀 Overview

The architecture follows a typical ML serving pipeline:

Client → API → Queue → Scheduler → Worker Pool → Model → Response

- API receives inference requests
- Requests are stored in a shared queue
- A scheduler forms batches of requests
- Worker threads process batches using a model
- Results are returned to the client

## 🎯 Key Features

- Request queue for handling concurrent inputs
- Static batching (mid-project)
- Worker pool for parallel processing
- Scheduler for batch formation
- End-to-end request handling with response mapping

## 📊 Future Enhancements (Final Phase)

- Dynamic batching based on system load
- Priority-based scheduling
- Backpressure handling under overload
- Performance metrics (latency, throughput, queue size)
- Load testing and evaluation

## 🛠️ Tech Stack

- Python
- FastAPI
- Threading / Concurrency
- PyTorch / Hugging Face (for inference)

## 📁 Project Structure
app/
core/ # request types, result store, startup
queueing/ # request queue
scheduler/ # batching + dispatch logic
workers/ # worker threads + pool
model/ # inference logic
main.py # FastAPI entrypoint


## 👥 Team 
- Brody Massad  
- Hung Truong 
- Ipsita Bhattacharjee  
- Sumanth Setty 

## ⚙️ Setup (to be added)
Instructions to run the system will be added after initial implementation.

## 📌 Notes
This project is part of **COMPSCI 532: Systems for Data Science** at UMass Amherst.