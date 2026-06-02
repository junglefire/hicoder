## 1. 项目骨架

- [x] 1.1 创建 `pyproject.toml`，声明项目名 `hicoder`、Python >=3.12、依赖 `agentscope`
- [x] 1.2 创建包目录结构：`hicoder/__init__.py`、`hicoder/config.py`、`hicoder/auth.py`
- [x] 1.3 创建内置默认配置文件 `config/default.toml`，包含 model、provider、approval_policy、sandbox_mode 默认值
- [x] 1.4 创建测试目录结构：`tests/__init__.py`、`tests/test_config.py`、`tests/conftest.py`

## 2. 配置系统（config-system spec）

- [x] 2.1 定义 `Config` pydantic BaseModel，包含字段：model、provider、api_key、approval_policy、sandbox_mode、cwd、hicoder_home、max_tokens
- [x] 2.2 实现 `ConfigLoader` 类，用 `tomllib` 读取 TOML 文件
- [x] 2.3 实现三层配置加载：内置 `config/default.toml` → `~/.hicoder/config.toml` → `.hicoder/config.toml`
- [x] 2.4 实现浅合并逻辑：后层非 None 值覆盖前层
- [x] 2.5 支持通过参数指定自定义配置文件路径
- [x] 2.6 编写测试：全三层存在时覆盖正确、仅内置默认时正常返回、缺失文件时不报错

## 3. API Key 认证（auth spec）

- [x] 3.1 实现 `resolve_api_key(provider, config_api_key)` 函数，复用 AgentScope `CredentialFactory` 按 provider 读取环境变量
- [x] 3.2 环境变量未设置时回退到 config_api_key
- [x] 3.3 两者均为空时抛出明确错误，提示应设置的环境变量名称
- [x] 3.4 在 Config 加载流程中集成 API Key 解析
- [x] 3.5 编写测试：环境变量优先、配置文件回退、缺失时错误提示、anthropic provider 专用变量
