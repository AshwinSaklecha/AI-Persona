# KV-Cache GitHub Project

Source repository: https://github.com/AshwinSaklecha/kv-cache

## Repository Summary

The project is a high-performance in-memory key-value cache server built with Python and asyncio and communicates over raw TCP sockets.

## Architecture Notes

- Network layer:
  - Async TCP server built on `asyncio.start_server()`
  - Handles concurrent client connections and non-blocking I/O
- Protocol layer:
  - Command parsing and response formatting
  - Supports commands like PUT, GET, DELETE, EXISTS, and QUIT
- Cache layer:
  - Core key-value store
  - TTL manager for expiration
  - LRU eviction policy

## Deployment and Performance

- The README describes an AWS deployment architecture with separate server and client EC2 instances inside a VPC.
- The default server port is 7171.
- The documented performance targets include more than 10,000 requests per second and mean latency below 1ms.

## Tooling and Testing

- Uses Docker for local containerization.
- Uses pytest-based tests for store, protocol, server, TTL, and eviction behavior.
- Includes load testing scripts with configurable connections, request counts, and workload ratios.

