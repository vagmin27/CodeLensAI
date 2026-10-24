# Node.js Event Loop Architecture

Node.js is an open-source, cross-platform JavaScript runtime environment built on Chrome's V8 JavaScript engine. It uses an event-driven, non-blocking I/O model that makes it lightweight and efficient for building scalable network applications.

## How the Event Loop Works

The event loop is what allows Node.js to perform non-blocking I/O operations despite JavaScript being single-threaded. It does this by offloading operations to the system kernel whenever possible. Since most modern kernels are multi-threaded, they can handle multiple operations executing in the background.

When one of these background operations completes, the kernel tells Node.js so that the appropriate callback may be added to the poll queue to eventually be executed.

## Phases of the Event Loop

The event loop consists of several distinct phases that repeat in cyclical order:

1. **Timers Phase**: Executes callbacks scheduled by setTimeout() and setInterval().
2. **Pending Callbacks Phase**: Executes I/O callbacks deferred to the next loop iteration (e.g., system-level errors like ECONNREFUSED).
3. **Idle, Prepare Phase**: Used internally by Node.js for internal house-keeping.
4. **Poll Phase**: Retrieves new I/O events, executes I/O related callbacks, and determines whether to block for incoming connections.
5. **Check Phase**: Executes setImmediate() callbacks immediately after the poll phase completes.
6. **Close Callbacks Phase**: Executes close callbacks, such as socket.on('close', ...).

## Microtask Queue: process.nextTick() and Promises

Between each phase of the event loop, Node.js checks its microtask queues:
- The `nextTickQueue` holds callbacks registered with `process.nextTick()`.
- The `promiseQueue` holds callbacks from resolved or rejected Promises.

Microtasks are always given priority and execute immediately after the current operation finishes, before the event loop advances to the next phase. Overusing `process.nextTick()` can starve the event loop by preventing it from ever reaching the poll phase.
