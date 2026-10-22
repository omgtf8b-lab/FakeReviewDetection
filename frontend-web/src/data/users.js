// ==========================================
// MOCK DATA FOR USER & ACCOUNT MANAGEMENT
// Week 7 - Fake Review Detection System
// ==========================================

export const ROLE_LABELS = {
  USER: 'Người dùng',
  SELLER: 'Người bán',
  ADMIN: 'Quản trị viên'
};

export const STATUS_LABELS = {
  ACTIVE: 'Đang hoạt động',
  LOCKED: 'Bị khóa'
};

export const initialMockUsers = [
  {
    id: 'USR001',
    fullName: 'Nguyễn Văn Minh',
    email: 'minh.nguyen@example.com',
    phone: '0912345678',
    role: 'USER',
    status: 'ACTIVE',
    createdAt: '15/01/2026',
    lastLogin: '02/10/2026 14:20',
    avatar: 'NM'
  },
  {
    id: 'USR002',
    fullName: 'Trần Thu Hà',
    email: 'ha.tran@example.com',
    phone: '0987654321',
    role: 'SELLER',
    status: 'ACTIVE',
    createdAt: '22/01/2026',
    lastLogin: '03/10/2026 09:15',
    avatar: 'TH',
    managedProducts: 18,
    totalReviews: 245
  },
  {
    id: 'USR003',
    fullName: 'Lê Quốc Bảo',
    email: 'bao.le@example.com',
    phone: '0933112233',
    role: 'USER',
    status: 'LOCKED',
    createdAt: '02/02/2026',
    lastLogin: '28/09/2026 18:40',
    avatar: 'QB'
  },
  {
    id: 'USR004',
    fullName: 'Phạm Minh Anh',
    email: 'anh.pham@example.com',
    phone: '0977889900',
    role: 'ADMIN',
    status: 'ACTIVE',
    createdAt: '10/02/2026',
    lastLogin: '03/10/2026 15:45',
    avatar: 'MA'
  },
  {
    id: 'USR005',
    fullName: 'Hoàng Tuấn Kiệt',
    email: 'kiet.hoang@example.com',
    phone: '0905123456',
    role: 'SELLER',
    status: 'ACTIVE',
    createdAt: '14/02/2026',
    lastLogin: '03/10/2026 11:30',
    avatar: 'TK',
    managedProducts: 32,
    totalReviews: 410
  },
  {
    id: 'USR006',
    fullName: 'Đỗ Thị Mai',
    email: 'mai.do@example.com',
    phone: '0944556677',
    role: 'USER',
    status: 'ACTIVE',
    createdAt: '20/02/2026',
    lastLogin: '01/10/2026 20:10',
    avatar: 'TM'
  },
  {
    id: 'USR007',
    fullName: 'Vũ Đức Trọng',
    email: 'trong.vu@example.com',
    phone: '0918273645',
    role: 'USER',
    status: 'LOCKED',
    createdAt: '28/02/2026',
    lastLogin: '25/09/2026 10:05',
    avatar: 'DT'
  },
  {
    id: 'USR008',
    fullName: 'Bùi Ngọc Lan',
    email: 'lan.bui@example.com',
    phone: '0966334455',
    role: 'SELLER',
    status: 'ACTIVE',
    createdAt: '05/03/2026',
    lastLogin: '02/10/2026 17:22',
    avatar: 'NL',
    managedProducts: 25,
    totalReviews: 312
  },
  {
    id: 'USR009',
    fullName: 'Đinh Công Thành',
    email: 'thanh.dinh@example.com',
    phone: '0922881199',
    role: 'USER',
    status: 'ACTIVE',
    createdAt: '12/03/2026',
    lastLogin: '03/10/2026 08:00',
    avatar: 'CT'
  },
  {
    id: 'USR010',
    fullName: 'Ngô Mỹ Duyên',
    email: 'duyen.ngo@example.com',
    phone: '0938765432',
    role: 'USER',
    status: 'ACTIVE',
    createdAt: '18/03/2026',
    lastLogin: '30/09/2026 21:50',
    avatar: 'MD'
  },
  {
    id: 'USR011',
    fullName: 'Lương Gia Huy',
    email: 'huy.luong@example.com',
    phone: '0971239876',
    role: 'SELLER',
    status: 'LOCKED',
    createdAt: '23/03/2026',
    lastLogin: '19/09/2026 14:12',
    avatar: 'GH',
    managedProducts: 12,
    totalReviews: 98
  },
  {
    id: 'USR012',
    fullName: 'Trịnh Phương Thảo',
    email: 'thao.trinh@example.com',
    phone: '0909876123',
    role: 'USER',
    status: 'ACTIVE',
    createdAt: '29/03/2026',
    lastLogin: '02/10/2026 19:35',
    avatar: 'PT'
  },
  {
    id: 'USR013',
    fullName: 'Võ Thanh Tùng',
    email: 'tung.vo@example.com',
    phone: '0919191919',
    role: 'ADMIN',
    status: 'ACTIVE',
    createdAt: '01/04/2026',
    lastLogin: '03/10/2026 16:10',
    avatar: 'TT'
  },
  {
    id: 'USR014',
    fullName: 'Phan Hải Đăng',
    email: 'dang.phan@example.com',
    phone: '0981122334',
    role: 'SELLER',
    status: 'ACTIVE',
    createdAt: '07/04/2026',
    lastLogin: '03/10/2026 13:05',
    avatar: 'HD',
    managedProducts: 40,
    totalReviews: 520
  },
  {
    id: 'USR015',
    fullName: 'Dương Thùy Linh',
    email: 'linh.duong@example.com',
    phone: '0945678901',
    role: 'USER',
    status: 'ACTIVE',
    createdAt: '15/04/2026',
    lastLogin: '01/10/2026 16:45',
    avatar: 'TL'
  }
];

export const initialCurrentUser = {
  id: 'USR000',
  fullName: 'Nguyễn Văn A',
  email: 'admin@example.com',
  phone: '0901234567',
  role: 'ADMIN',
  status: 'ACTIVE',
  avatar: 'VA',
  department: 'Trung tâm Vận hành Hệ thống',
  lastLogin: '03/10/2026 16:30',
  device: 'Chrome trên Windows',
  ipAddress: '113.190.234.12 (Hà Nội, Việt Nam)',
  createdAt: '01/01/2026'
};
