import asyncio
import json

from ltclaw_gy_x.constant import WORKING_DIR
from ltclaw_gy_x.game.service import GameService


async def main() -> None:
    workspace_dir = WORKING_DIR / "workspaces" / "default"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    service = GameService(workspace_dir)
    await service.start()
    try:
        result = await service.force_full_rescan()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
