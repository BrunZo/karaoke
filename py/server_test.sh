curl -X POST -H "Content-Type: application/json" -d '{"name": "Ulises"}' http://127.0.0.1:8000/register
curl -X POST -H "Content-Type: application/json" -d '{"name": "Bruno"}' http://127.0.0.1:8000/register
curl -X POST -H "Content-Type: application/json" -d '{"name": "Hoch"}' http://127.0.0.1:8000/register
curl -X POST -H "Content-Type: application/json" -d '{"name": "Ulises"}' http://127.0.0.1:8000/enqueue
curl -X POST -H "Content-Type: application/json" -d '{"name": "Bruno"}' http://127.0.0.1:8000/enqueue
curl -X POST -H "Content-Type: application/json" -d '{}' http://127.0.0.1:8000/dequeue
curl -X POST -H "Content-Type: application/json" -d '{"name": "Ulises"}' http://127.0.0.1:8000/enqueue
curl -X POST -H "Content-Type: application/json" -d '{"name": "Hoch"}' http://127.0.0.1:8000/enqueue
curl -X POST -H "Content-Type: application/json" -d '{"jury": 0, "score": 10}' http://127.0.0.1:8000/send_score
curl -X POST -H "Content-Type: application/json" -d '{"jury": 1, "score": 8}' http://127.0.0.1:8000/send_score
curl -X POST -H "Content-Type: application/json" -d '{"jury": 2, "score": 7}' http://127.0.0.1:8000/send_score
curl -X POST -H "Content-Type: application/json" -d '{}' http://127.0.0.1:8000/commit_scores
