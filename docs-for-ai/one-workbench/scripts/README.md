# scripts/

本 task 的确定性脚本目录。当前为空。

计划中的脚本（P0 后再加）：
- `probe-pi-rpc.ts` — 起一个 `pi --mode rpc`，发 `get_state` 并打印首帧，用于验证子进程可用性。
- `record-events.ts` — 录制 JSONL 事件流，做 `pi-bridge` 回放测试的 fixture。
