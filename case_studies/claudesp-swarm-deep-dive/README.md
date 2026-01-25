# claudesp Swarm Deep Dive

How 10 AI agents built a macOS app in 13 minutes using claude-sneakpeek's swarm mode.

## What is claudesp?

[claude-sneakpeek](https://github.com/mikekelly/claude-sneakpeek) (claudesp) is a tool that enables multi-agent orchestration with Claude. Its "swarm mode" spawns multiple parallel agents that coordinate via:

- **Teammate() tool** - Core coordination primitive for agent communication
- **Inbox-based messaging** - Loose coupling via JSON files
- **blockedBy dependencies** - Enforced execution order forming a DAG
- **Graceful shutdown protocol** - Two-phase termination

## The Case Study

In one 13-minute session, claudesp orchestrated 10 specialized agents to build **AgentControlTower** - a complete macOS Menu Bar app with:

- 22 Swift source files
- 6 build/distribution scripts
- SwiftUI interface with hotkey support
- Sparkle auto-update integration
- Verified build: `swift build` ✅

## Key Patterns Covered

1. **Swarm Architecture** - Team lead + specialized worker agents
2. **Dependency Management** - blockedBy enforces correct execution order
3. **Parallel Execution** - Agents work proactively, not just reactively
4. **Conflict Resolution** - Automatic detection and resolution when agents create same files
5. **Graceful Shutdown** - Request → Approve two-phase protocol
6. **Reference Implementation** - Porting patterns from existing codebase
7. **Continuous Build Verification** - Catching errors early

## Files

- [SwarmDeepDive.pdf](./20260125_EDU_AIProductEngineer_S2E5_SwarmDeepDive.pdf) - Full presentation slides
- [claudesp_swarm_log.txt](./claudesp_swarm_log.txt) - Raw execution log showing all agent coordination, tool calls, and message passing

## Resources

- [claude-sneakpeek](https://github.com/mikekelly/claude-sneakpeek) - The tool
- [Workshop 5: Voice, Context & Orchestration](../../lesson5/) - Parent workshop materials
