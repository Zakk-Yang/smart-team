# Multi-Agent System Architecture

```mermaid
sequenceDiagram
    participant User
    participant Orchestrator
    participant Agent1
    participant Agent2
    participant FunctionExecutor
    participant SharedContext

    User->>Orchestrator: Send Request
    
    rect rgb(200, 220, 255)
        Note over Orchestrator: Task Analysis
        Orchestrator->>SharedContext: Check History
        SharedContext-->>Orchestrator: Return Context
    end

    alt Task Type 1
        Orchestrator->>Agent1: Transfer Control
        
        rect rgb(220, 200, 255)
            Note over Agent1: Process Task Type 1
            Agent1->>SharedContext: Load Context
            SharedContext-->>Agent1: Return Context
            
            loop Batch Execution
                Agent1->>FunctionExecutor: Execute Functions
                FunctionExecutor-->>Agent1: Return Results
                Agent1->>SharedContext: Update Context
            end
        end
        
        alt Needs Agent2
            Agent1->>Agent2: Transfer for Subtask
            
            rect rgb(200, 255, 220)
                Note over Agent2: Process Subtask
                Agent2->>SharedContext: Load Context
                Agent2->>FunctionExecutor: Execute Functions
                FunctionExecutor-->>Agent2: Return Results
                Agent2->>SharedContext: Update Context
            end
            
            Agent2->>Agent1: Return Control
        end
        
        Agent1->>Orchestrator: Return Control
    else Task Type 2
        Orchestrator->>Agent2: Transfer Control
        
        rect rgb(200, 255, 220)
            Note over Agent2: Process Task Type 2
            Agent2->>SharedContext: Load Context
            SharedContext-->>Agent2: Return Context
            Agent2->>FunctionExecutor: Execute Functions
            FunctionExecutor-->>Agent2: Return Results
            Agent2->>SharedContext: Update Context
        end
        
        Agent2->>Orchestrator: Return Control
    end

    Orchestrator-->>User: Return Response
```

## System Flow Example

1. **Initial Request Handling**
   - User sends request to Orchestrator
   - Orchestrator analyzes task type and context
   - Decides whether to route to Agent1 or Agent2

2. **Agent Interaction Patterns**
   - **Pattern 1: Direct Processing**
     * Orchestrator → Agent2 → Orchestrator
     * Used for simple, single-agent tasks
   
   - **Pattern 2: Agent Collaboration**
     * Orchestrator → Agent1 → Agent2 → Agent1 → Orchestrator
     * Used for complex tasks requiring multiple agents

3. **Context Management**
   - SharedContext maintains system state
   - All agents access the same context
   - History tracked across agent transfers

4. **Function Execution**
   - Agents can execute functions in batches
   - Results update shared context
   - State maintained throughout process

## Implementation Notes

- **Agent1 Example**: Could handle complex tasks requiring batch processing
- **Agent2 Example**: Could handle simpler, single-function tasks
- Both agents follow same context-sharing protocol
- System can be extended with more agents following these patterns
