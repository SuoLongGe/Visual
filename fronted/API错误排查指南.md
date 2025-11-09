# API 错误排查指南

## 🔍 常见错误及解决方案

### 错误 1: `API请求失败: AxiosError`

**可能原因：**
1. 后端服务未启动
2. 网络连接问题
3. CORS 跨域问题
4. 请求 URL 配置错误

**解决步骤：**

#### 步骤 1: 检查后端服务是否运行

```powershell
# 检查端口 5001 是否被占用（注意：后端端口是 5001，不是 5000）
netstat -ano | findstr :5001
```

如果看到 `LISTENING` 状态，说明后端服务正在运行。

如果没有运行，启动后端服务：
```powershell
cd ..
python app.py
```

#### 步骤 2: 测试 API 是否可访问

在浏览器中直接访问：
```
http://localhost:5001/api/industry/ranking/jobs
```

或者在 PowerShell 中测试：
```powershell
Invoke-WebRequest -Uri http://localhost:5001/api/industry/ranking/jobs -UseBasicParsing
```

如果返回 JSON 数据，说明 API 正常。

#### 步骤 3: 检查前端配置

1. **检查 Vite 代理配置** (`vite.config.js`)
   ```javascript
   proxy: {
     '/api': {
       target: 'http://localhost:5001',
       changeOrigin: true,
       timeout: 30000  // 代理超时时间30秒
     }
   }
   ```

2. **检查 API 基础 URL** (`src/config/appConfig.js`)
   ```javascript
   baseURL: '/api'  // 使用相对路径，通过 Vite 代理
   ```

3. **如果代理不工作，可以尝试直接访问**：
   ```javascript
   baseURL: 'http://localhost:5001/api'  // 直接访问（注意端口是5001）
   ```

#### 步骤 4: 查看浏览器控制台详细错误

打开浏览器开发者工具（F12），查看：
- **Console 标签**：查看详细的错误信息
- **Network 标签**：查看请求的 URL、状态码、响应内容

现在错误处理已经改进，会显示：
- 请求的完整 URL
- 错误状态码
- 详细的错误信息

### 错误 2: `无法连接到服务器`

**原因：** 后端服务未启动或端口被占用

**解决方案：**
1. 启动后端服务：`python app.py`
2. 检查端口是否被其他程序占用
3. 如果端口被占用，可以修改后端端口或关闭占用端口的程序

### 错误 3: `CORS 跨域错误`

**原因：** 浏览器阻止了跨域请求

**解决方案：**
后端已经配置了 CORS，如果仍然出现此错误：
1. 检查 `app.py` 中是否启用了 `CORS(app)`
2. 确保使用 Vite 代理（推荐）或后端 CORS 配置正确

### 错误 4: `timeout of 10000ms exceeded` 或 `ECONNABORTED`

**原因：** 请求超时，后端处理时间过长（超过10秒）

**可能原因：**
1. Excel 文件很大，读取和处理需要较长时间
2. 后端服务响应慢
3. 网络连接问题

**解决方案：**

1. **已自动增加超时时间到30秒**
   - 前端超时时间已从10秒增加到30秒
   - Vite 代理超时时间也已增加到30秒

2. **检查后端服务状态**
   ```powershell
   # 检查后端服务是否运行
   netstat -ano | findstr :5001
   ```

3. **查看后端日志**
   - 后端已添加详细日志，可以查看处理进度
   - 如果看到"正在读取Excel文件..."但长时间无响应，可能是文件太大

4. **重启服务**
   - 重启前端服务（配置已更新）
   - 如果问题持续，重启后端服务

5. **如果仍然超时**
   - 检查 Excel 文件大小
   - 考虑优化数据处理逻辑
   - 可以进一步增加超时时间（在 `appConfig.js` 中修改）

### 错误 5: `geo3D exists` 警告

**说明：** 这是 ECharts 的警告信息，不是错误，可以忽略。

这是 ECharts GL 插件注册时的正常提示，不影响功能。

---

## 🛠️ 调试技巧

### 1. 启用详细日志

错误处理已经改进，现在会在控制台显示：
- 请求的完整 URL
- 请求方法
- 错误状态码
- 服务器返回的错误信息

### 2. 使用浏览器 Network 标签

1. 打开开发者工具（F12）
2. 切换到 **Network** 标签
3. 点击"加载职位排名数据"按钮
4. 查看请求详情：
   - **Request URL**: 检查请求的完整 URL
   - **Status**: 检查状态码（200 表示成功）
   - **Response**: 查看服务器返回的数据

### 3. 直接测试 API

在浏览器地址栏输入：
```
http://localhost:5001/api/industry/ranking/jobs
```

如果能看到 JSON 数据，说明 API 正常，问题在前端配置。

---

## 📋 检查清单

- [ ] 后端服务正在运行（端口 5001）
- [ ] 可以直接访问 API（浏览器输入 URL）
- [ ] 前端 Vite 开发服务器正在运行（端口 3000）
- [ ] 浏览器控制台没有 CORS 错误
- [ ] Network 标签显示请求已发送
- [ ] 请求 URL 正确（`/api/industry/ranking/jobs`）

---

## 🔧 快速修复

如果以上步骤都正常，但仍然出错，尝试：

1. **重启前端服务**
   ```powershell
   # 停止当前服务（Ctrl+C）
   # 重新启动
   npm run dev
   ```

2. **清除浏览器缓存**
   - 按 `Ctrl + Shift + Delete`
   - 清除缓存和 Cookie
   - 刷新页面

3. **检查防火墙**
   - 确保防火墙没有阻止本地连接

4. **使用不同的浏览器**
   - 尝试 Chrome、Firefox 或 Edge

---

## 📞 获取帮助

如果问题仍然存在，请提供以下信息：

1. 浏览器控制台的完整错误信息
2. Network 标签中的请求详情（截图）
3. 后端服务的日志输出
4. 操作系统和浏览器版本

