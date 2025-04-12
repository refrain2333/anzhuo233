/**
 * 智慧校园学习助手系统
 * 主JavaScript文件 - 提供通用功能
 */

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    console.log('智慧校园学习助手系统前端加载完成');
    
    // 检查登录状态，更新导航栏
    function checkLoginStatus() {
        const token = localStorage.getItem('auth_token');
        const loginLink = document.querySelector('a[href="/login"]');
        const registerLink = document.querySelector('a[href="/register"]');
        
        if (token) {
            // 已登录状态，修改导航栏
            if (loginLink && loginLink.parentNode) {
                const userLink = document.createElement('a');
                userLink.href = '#';
                userLink.textContent = '个人中心';
                loginLink.parentNode.innerHTML = '';
                loginLink.parentNode.appendChild(userLink);
            }
            
            if (registerLink && registerLink.parentNode) {
                const logoutLink = document.createElement('a');
                logoutLink.href = '#';
                logoutLink.textContent = '退出登录';
                logoutLink.addEventListener('click', function(e) {
                    e.preventDefault();
                    logout();
                });
                registerLink.parentNode.innerHTML = '';
                registerLink.parentNode.appendChild(logoutLink);
            }
        }
    }
    
    // 退出登录
    function logout() {
        localStorage.removeItem('auth_token');
        showMessage('已退出登录', 'info');
        setTimeout(() => {
            window.location.href = '/';
        }, 1000);
    }
    
    // 检查登录状态
    checkLoginStatus();
    
    // 通用消息弹窗函数
    window.showMessage = function(message, type = 'info') {
        // 如果已存在消息框则移除
        const existingMsg = document.querySelector('.message-box');
        if (existingMsg) {
            existingMsg.remove();
        }
        
        // 创建新消息框
        const msgBox = document.createElement('div');
        msgBox.className = `message-box message-${type}`;
        msgBox.textContent = message;
        
        // 添加关闭按钮
        const closeBtn = document.createElement('span');
        closeBtn.className = 'message-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.addEventListener('click', function() {
            msgBox.remove();
        });
        
        msgBox.appendChild(closeBtn);
        document.body.appendChild(msgBox);
        
        // 5秒后自动关闭
        setTimeout(function() {
            if (msgBox.parentNode) {
                msgBox.remove();
            }
        }, 5000);
    };
    
    // 添加消息框样式
    const style = document.createElement('style');
    style.textContent = `
        .message-box {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 4px;
            color: white;
            z-index: 9999;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            justify-content: space-between;
            min-width: 250px;
        }
        .message-info {
            background-color: #2196F3;
        }
        .message-success {
            background-color: #4CAF50;
        }
        .message-warning {
            background-color: #FF9800;
        }
        .message-error {
            background-color: #F44336;
        }
        .message-close {
            margin-left: 15px;
            font-weight: bold;
            cursor: pointer;
            font-size: 18px;
        }
    `;
    document.head.appendChild(style);
    
    // 检测API状态
    fetch('/health')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                console.log('API服务正常运行');
            } else {
                console.warn('API服务异常');
                showMessage('API服务异常，部分功能可能无法使用', 'warning');
            }
        })
        .catch(error => {
            console.error('API连接失败', error);
            showMessage('无法连接到API服务', 'error');
        });
    
    // 通用表单提交处理
    document.querySelectorAll('form[data-api-form]').forEach(form => {
        form.addEventListener('submit', async function(event) {
            event.preventDefault();
            
            const url = this.getAttribute('action');
            const method = this.getAttribute('method') || 'POST';
            
            const formData = new FormData(this);
            const data = {};
            formData.forEach((value, key) => {
                data[key] = value;
            });
            
            try {
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showMessage(result.message || '操作成功', 'success');
                    // 触发自定义事件
                    const event = new CustomEvent('api-form-success', { detail: result });
                    this.dispatchEvent(event);
                } else {
                    showMessage(result.message || '操作失败', 'error');
                }
            } catch (error) {
                showMessage('请求错误: ' + error.message, 'error');
                console.error('表单提交错误', error);
            }
        });
    });
}); 