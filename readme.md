 docker compose up -d                          # Start DB services
  cd backend && pip install -e ".[dev]"         # Install backend deps
  cp .env.example .env                          # Configure environment                                                                                                                                    
  alembic upgrade head                          # Run migrations
  python -m scripts.seed_courses                # Seed sample data                                                                                                                                         
  uvicorn src.main:app --reload --port 8000     # Start backend
                                                                                                                                                                                                           
  cd frontend && npm install && npm run dev     # Start frontend                                                                                                                                           
 