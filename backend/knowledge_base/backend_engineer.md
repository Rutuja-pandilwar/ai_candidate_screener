# Backend Engineering Knowledge Base

## Chapter 1: API Architecture and Protocols
- **REST (Representational State Transfer)**: Architectural style relying on stateless, client-server communication using HTTP standard methods:
  - `GET`: Safe, idempotent retrieval.
  - `POST`: Create resource. Non-idempotent.
  - `PUT`: Update/replace resource. Idempotent.
  - `PATCH`: Partial update. Non-idempotent (typically).
  - `DELETE`: Remove resource. Idempotent.
  - **Status Codes**: 200 (OK), 201 (Created), 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), 500 (Internal Server Error).
- **GraphQL**: Query language for APIs that allows clients to request exactly the data they need. Reduces over-fetching and under-fetching. Uses a single endpoint (`POST /graphql`) and maps requests to a strongly-typed schema.
- **gRPC**: High-performance RPC framework developed by Google. Uses HTTP/2 for transport and Protocol Buffers (Protobuf) for serialization. Supports streaming APIs and provides low-latency communication.

## Chapter 2: Databases and Data Modeling
- **Relational Databases (RDBMS)**: Use structured tables with primary/foreign keys. Strong consistency guarantees (ACID).
  - **ACID Properties**:
    - **Atomicity**: All operations in a transaction succeed or all fail.
    - **Consistency**: Database transitions from one valid state to another.
    - **Isolation**: Concurrent transactions execute without interference.
    - **Durability**: Committed changes are permanent, surviving crashes.
  - **Normalization**: Reducing redundancy and dependency by organizing fields and table relations:
    - **1NF**: Atomic values, no repeating groups.
    - **2NF**: In 1NF and all non-key attributes are fully dependent on the primary key.
    - **3NF**: In 2NF and no transitive dependencies.
  - **Denormalization**: Intentionally introducing redundancy to optimize read performance in read-heavy applications.
- **NoSQL Databases**:
  - **Document (MongoDB)**: Stores JSON-like documents. Highly flexible schema.
  - **Key-Value (Redis)**: Ultra-fast, in-memory data store.
  - **Wide-Column (Cassandra)**: Distributed, highly scalable write-optimized database.
  - **Graph (Neo4j)**: Optimized for traversing connections/nodes.
- **CAP Theorem**: In a distributed system, you can only guarantee two out of three:
  - **Consistency**: Every read receives the most recent write or an error.
  - **Availability**: Every request receives a non-error response.
  - **Partition Tolerance**: System continues to operate despite network partition/node failures.

## Chapter 3: Caching, Message Queues & Distributed Systems
- **Caching**: Storing copies of data in high-speed storage (Redis, Memcached) to reduce database load.
  - **Caching Strategies**:
    - **Cache-Aside (Lazy Loading)**: App checks cache; on miss, reads from DB and writes to cache.
    - **Write-Through**: App writes to cache, which writes to DB immediately.
    - **Write-Behind (Write-Back)**: App writes to cache; cache writes to DB asynchronously.
  - **Cache Eviction Policies**: Least Recently Used (LRU), Least Frequently Used (LFU), First In First Out (FIFO).
- **Message Queues**: Decouple components asynchronously (producer-consumer pattern).
  - **RabbitMQ**: Message broker supporting complex routing via exchanges (direct, topic, fanout).
  - **Apache Kafka**: Distributed streaming platform storing messages as an append-only commit log on disk. High throughput, supports replayability.
- **Concurrency & Parallelism**:
  - **Concurrency**: Managing multiple tasks at once (interleaved execution, e.g. async/await in Python or Node.js).
  - **Parallelism**: Running multiple tasks at the exact same time (multi-threading or multi-processing on multi-core CPUs).

## Chapter 4: Authentication, Authorization & Security
- **Authentication**: Verifying who a user is (e.g. Passwords, MFA).
- **Authorization**: Verifying what a user has permission to do (RBAC, ABAC).
- **JWT (JSON Web Token)**: Standard for securely transmitting info as a JSON object. Signed using a secret (HMAC) or public/private key (RSA/ECDSA). Components: `Header.Payload.Signature`. Stateless token, but difficult to revoke before expiration.
- **OAuth 2.0 / OIDC**: Protocol framework for delegated authorization. OIDC extends OAuth 2.0 to add identity/authentication via ID tokens.
- **OWASP Top 10 Vulnerabilities**:
  - **SQL Injection**: Injecting malicious SQL commands. Mitigated by using parameterized queries/ORMs.
  - **XSS (Cross-Site Scripting)**: Injecting malicious scripts into web pages. Mitigated by escaping input.
  - **CSRF (Cross-Site Request Forgery)**: Unauthorized commands executed from a trusted user. Mitigated by CSRF tokens and SameSite cookies.
