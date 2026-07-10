// Admin UI helper
(async function(){
    function el(id){ return document.getElementById(id); }

    async function loadUsers(){
        const container = el('users-container');
        if(!container) return;
        container.innerHTML = 'جاري التحميل...';
        try{
            const resp = await AuthManager.fetchWithAuth('/api/admin/users');
            if(!resp.ok) throw new Error('Failed');
            const users = await resp.json();
            if(!users.length){
                container.innerHTML = '<div class="text-muted">لا يوجد مستخدمين</div>';
                return;
            }
            container.innerHTML = `
                <table class="table">
                    <thead><tr><th>اسم المستخدم</th><th>البريد</th><th>الدور</th><th>الإجراءات</th></tr></thead>
                    <tbody id="users-tbody"></tbody>
                </table>
            `;
            const tbody = el('users-tbody');
            tbody.innerHTML = users.map(u => `
                <tr>
                    <td>${u.username}</td>
                    <td>${u.email}</td>
                    <td><select data-id="${u.id}" class="form-select form-select-sm role-select"><option value="user" ${u.role==='user'?'selected':''}>user</option><option value="admin" ${u.role==='admin'?'selected':''}>admin</option></select></td>
                    <td><button class="btn btn-sm btn-danger delete-user" data-id="${u.id}">حذف</button></td>
                </tr>
            `).join('');

            // attach listeners
            document.querySelectorAll('.role-select').forEach(s => s.addEventListener('change', async (e)=>{
                const id = e.target.dataset.id;
                const role = e.target.value;
                await AuthManager.fetchWithAuth(`/api/admin/users/${id}/role`, {method: 'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify({role})});
            }));
            document.querySelectorAll('.delete-user').forEach(b=>b.addEventListener('click', async (e)=>{
                const id = e.target.dataset.id;
                if(!confirm('حذف المستخدم؟')) return;
                await AuthManager.fetchWithAuth(`/api/admin/users/${id}`, {method: 'DELETE'});
                loadUsers();
            }));
        }catch(err){
            container.innerHTML = '<div class="text-danger">فشل تحميل المستخدمين</div>';
            console.error(err);
        }
    }

    async function loadSessions(){
        const container = el('sessions-container');
        if(!container) return;
        container.innerHTML = 'جاري التحميل...';
        try{
            const resp = await AuthManager.fetchWithAuth('/api/admin/sessions');
            if(!resp.ok) throw new Error('Failed');
            const sessions = await resp.json();
            if(!sessions.length){
                container.innerHTML = '<div class="text-muted">لا توجد جلسات</div>';
                return;
            }
            container.innerHTML = `
                <table class="table">
                    <thead><tr><th>المستخدم</th><th>بداية</th><th>نهاية</th><th>المدة</th><th>إرهاق متوسط</th><th>تنبيهات</th><th>إجراءات</th></tr></thead>
                    <tbody>${sessions.map(s=>`<tr>
                        <td>${s.username}</td>
                        <td>${new Date(s.start_time).toLocaleString('ar-EG')}</td>
                        <td>${s.end_time? new Date(s.end_time).toLocaleString('ar-EG') : '-'}</td>
                        <td>${s.end_time? Math.round((new Date(s.end_time)-new Date(s.start_time))/60000) + ' دقيقة' : '-'}</td>
                        <td>${s.fatigue_avg}</td>
                        <td>${s.alerts_count}</td>
                        <td><button data-id="${s.id}" class="btn btn-sm btn-danger delete-session">حذف</button></td>
                    </tr>`).join('')}</tbody>
                </table>
            `;
            document.querySelectorAll('.delete-session').forEach(b=>b.addEventListener('click', async (e)=>{
                const id = e.target.dataset.id;
                if(!confirm('حذف الجلسة؟')) return;
                await AuthManager.fetchWithAuth(`/api/admin/sessions/${id}`, {method: 'DELETE'});
                loadSessions();
            }));
        }catch(err){
            container.innerHTML = '<div class="text-danger">فشل تحميل الجلسات</div>';
            console.error(err);
        }
    }

    async function loadStats(){
        const elUser = el('user-count');
        if(!elUser) return;
        try{
            const resp = await AuthManager.fetchWithAuth('/api/admin/stats');
            if(!resp.ok) throw new Error('Failed');
            const s = await resp.json();
            el('user-count').innerText = s.user_count ?? 0;
            el('session-count').innerText = s.session_count ?? 0;
            el('total-alerts').innerText = s.total_alerts ?? 0;
            el('avg-fatigue').innerText = (s.avg_fatigue ?? 0) + '%';
        }catch(err){
            console.error(err);
        }
    }

    document.addEventListener('DOMContentLoaded', ()=>{
        // decide which loader to run based on presence of containers
        if(el('users-container')) loadUsers();
        if(el('sessions-container')) loadSessions();
        if(el('admin-stats')) loadStats();
    });
})();
