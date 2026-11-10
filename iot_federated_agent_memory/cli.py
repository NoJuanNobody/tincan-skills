import argparse
import json
import sys
from .scale import IoTFederatedMemoryScale


def main() -> int:
    # `python3 -m iot_federated_agent_memory.cli tui [...]` launches the terminal app;
    # `python3 -m iot_federated_agent_memory.cli tincan [...]` launches the TinCan CLI;
    # everything else keeps the original scale-report behaviour.
    if len(sys.argv) > 1 and sys.argv[1] in ("tui", "screensaver"):
        from .tui import main as tui_main
        extra = ["--screensaver"] if sys.argv[1] == "screensaver" else []
        return tui_main(extra + sys.argv[2:])

    if len(sys.argv) > 1 and sys.argv[1] in ("tincan", "tc"):
        from .tincan_cli import main as tincan_main
        return tincan_main(sys.argv[2:])

    parser = argparse.ArgumentParser(
        prog="iot-memory-scale",
        description="Evaluate the Multi-Account Gemini + Antigravity + Grok Shared Setup and Future IoT Research Scale",
    )
    parser.add_argument(
        "--vault-dir",
        default="/Users/alejandrolondono/dev/vault-graphrag-paywall/vault_data",
        help="Path to the shared Obsidian Vault directory",
    )
    parser.add_argument(
        "--pool-json",
        default="/Users/alejandrolondono/dev/gemini-activity-harvester/scrapes/shared_gemini_pool.json",
        help="Path to pooled multi-account Gemini JSON",
    )
    args = parser.parse_args()

    scale = IoTFederatedMemoryScale(
        vault_dir=args.vault_dir,
        harvester_pool_path=args.pool_json,
    )
    report = scale.evaluate_current_and_future()
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
