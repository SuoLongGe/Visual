# Node.js 安装指南（Windows）

## 方法一：官方安装程序（推荐）

### 步骤 1：下载 Node.js
1. 访问 Node.js 官网：**https://nodejs.org/**
2. 点击下载 **LTS 版本**（长期支持版本，更稳定）
3. 选择 **Windows Installer (.msi)** - 64-bit

### 步骤 2：安装 Node.js
1. 双击下载的 `.msi` 文件
2. 点击 "Next" 继续
3. **重要**：勾选 "Automatically install the necessary tools"（自动安装必要工具）
4. 点击 "Install" 开始安装
5. 等待安装完成

### 步骤 3：验证安装
**关闭当前 PowerShell 窗口，打开新的 PowerShell 窗口**，然后运行：

```powershell
node --version
npm --version
```

如果显示版本号（如 `v20.10.0` 和 `10.2.3`），说明安装成功！

### 步骤 4：安装前端依赖
```powershell
cd fronted
npm install
```

### 步骤 5：启动前端服务
```powershell
npm run dev
```

---

## 方法二：使用 Chocolatey（如果已安装）

如果你已经安装了 Chocolatey 包管理器：

```powershell
choco install nodejs-lts
```

---

## 方法三：使用 winget（Windows 10/11）

```powershell
winget install OpenJS.NodeJS.LTS
```

---

## 常见问题解决

### 问题 1：安装后仍然提示 "npm 无法识别"

**解决方案：**
1. **完全关闭所有 PowerShell 窗口**
2. **重新打开新的 PowerShell 窗口**
3. 再次尝试 `npm --version`

如果还是不行：
1. 检查环境变量：
   - 按 `Win + R`，输入 `sysdm.cpl`，回车
   - 点击 "高级" 标签
   - 点击 "环境变量"
   - 在 "系统变量" 中找到 `Path`
   - 确认包含：`C:\Program Files\nodejs\`
2. 如果不存在，手动添加后重启电脑

### 问题 2：安装速度慢

**使用国内镜像加速：**

安装完 Node.js 后，运行：
```powershell
npm config set registry https://registry.npmmirror.com
```

### 问题 3：权限问题

如果遇到权限错误，以管理员身份运行 PowerShell：
1. 右键点击 PowerShell
2. 选择 "以管理员身份运行"
3. 再次尝试安装命令

---

## 快速检查清单

- [ ] 已下载 Node.js 安装程序
- [ ] 已运行安装程序并完成安装
- [ ] **已关闭并重新打开 PowerShell**
- [ ] `node --version` 显示版本号
- [ ] `npm --version` 显示版本号
- [ ] 已运行 `npm install` 安装依赖
- [ ] 已运行 `npm run dev` 启动服务

---

## 安装完成后

安装完成后，在 `fronted` 目录下运行：

```powershell
# 1. 安装依赖（首次需要）
npm install

# 2. 启动开发服务器
npm run dev
```

然后访问：**http://localhost:3000**

