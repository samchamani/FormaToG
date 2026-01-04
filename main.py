# import argparse
# from agents.registry import provider
# from graphs.registry import getGraph, graphs
# from methods.tog import think_on_graph


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--prompt", type=str, help="Question to ask the system")
#     parser.add_argument(
#         "--agent_provider",
#         choices=[p for p in provider.keys()],
#         required=True,
#         help="The service that provides the language model (ollama, google, ..)",
#     )
#     parser.add_argument(
#         "--agent",
#         type=str,
#         required=True,
#         help="Language Model to use as agent (must be available through agent provider)",
#     )
#     parser.add_argument(
#         "--graph",
#         choices=graphs,
#         help="The knowledge graph to use",
#     )
#     parser.add_argument(
#         "--max-paths",
#         type=int,
#         help="The maximum number of best paths to maintain",
#     )
#     parser.add_argument(
#         "--max-depth",
#         type=int,
#         help="The maximum number of jumps allowed",
#     )

#     args = parser.parse_args()
#     print(f"Prompt: {args.prompt}")
#     print(f"Agent: {args.agent}")
#     print(f"Graph: {args.graph}")
#     print(f"Maximum jumps within path: {args.max_depth}")
#     print(f"Maximum top paths maintained: {args.max_paths}")
#     print("\n\n")

#     answer = think_on_graph(
#         prompt=args.prompt,
#         agent=provider[args.agent_provider](model=args.agent),
#         graph=getGraph(args.graph),
#         max_paths=args.max_paths,
#         max_depth=args.max_depth,
#         topic_entities=[],
#     )

#     print("\nThink-on-Graph answer:")
#     print(answer)
