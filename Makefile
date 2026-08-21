.PHONY: setup build check clean

# Four dependency systems, one per server runtime. `setup` brings all of them up
# from a fresh clone; `check` proves each server actually speaks MCP.

setup: .venv servers/linkedin/.venv servers/x/node_modules build

.venv:
	python3 -m venv .venv
	./.venv/bin/pip install -q -r requirements.txt

servers/linkedin/.venv:
	cd servers/linkedin && uv sync

servers/x/node_modules:
	cd servers/x && npm install

build: servers/x/dist servers/xiaohongshu/bin/xiaohongshu-mcp

servers/x/dist: servers/x/node_modules
	cd servers/x && npm run build

servers/xiaohongshu/bin/xiaohongshu-mcp:
	cd servers/xiaohongshu && go build -o bin/xiaohongshu-mcp .

# xiaohongshu speaks HTTP, not stdio — it has to be running before Claude Code
# can reach it. The other four are spawned on demand.
xhs:
	cd servers/xiaohongshu && ./bin/xiaohongshu-mcp -headless=true

check:
	@claude mcp list 2>&1 | grep claude-toolkit || echo "no plugin servers found"

clean:
	rm -rf servers/x/dist servers/x/node_modules
	rm -rf servers/xiaohongshu/bin
	rm -rf servers/linkedin/.venv
	rm -rf .venv
	find . -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} +
