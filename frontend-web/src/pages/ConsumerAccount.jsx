import React,{useEffect,useState} from 'react';
import {api} from '../lib/api';
import {useAuth} from '../contexts/AuthContext';

export default function ConsumerAccount(){
  const {user,logout}=useAuth();const [profile,setProfile]=useState(null);const [message,setMessage]=useState('');const [busy,setBusy]=useState(false);
  useEffect(()=>{let active=true;api.get('/api/workspace/profile').then(v=>{if(active)setProfile(v);}).catch(e=>{if(active)setMessage(e.message);});return()=>{active=false;};},[]);
  async function save(e){e.preventDefault();setBusy(true);try{await api.put('/api/workspace/profile',profile);setMessage('Đã lưu hồ sơ.');}catch(e){setMessage(e.message);}finally{setBusy(false);}}
  async function password(e){e.preventDefault();const data=new FormData(e.currentTarget);setBusy(true);try{await api.post('/api/workspace/password',{current_password:data.get('current_password'),new_password:data.get('new_password')});logout();}catch(e){setMessage(e.message);}finally{setBusy(false);}}
  return <div style={{maxWidth:680,margin:'auto'}}><h1>Tài khoản của tôi</h1><p>{user?.email}</p><p role="status">{message}</p><section className="card">{profile&&<form className="work-form" onSubmit={save}><label>Tên hiển thị<input required minLength={2} value={profile.display_name||''} onChange={e=>setProfile({...profile,display_name:e.target.value})}/></label><label>Điện thoại (tùy chọn)<input value={profile.phone||''} onChange={e=>setProfile({...profile,phone:e.target.value})}/></label><button className="btn btn-primary" disabled={busy}>Lưu hồ sơ</button></form>}</section><section className="card" style={{marginTop:20}}><h2>Đổi mật khẩu</h2><form className="work-form" onSubmit={password}><label>Mật khẩu hiện tại<input type="password" name="current_password" required autoComplete="current-password"/></label><label>Mật khẩu mới<input type="password" name="new_password" required minLength={8} autoComplete="new-password"/></label><p>Đổi mật khẩu sẽ thu hồi các phiên đăng nhập cũ.</p><button className="btn btn-primary" disabled={busy}>Đổi mật khẩu</button></form></section></div>;
}
