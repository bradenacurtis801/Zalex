'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { authApi } from '@/api'
import { Button } from '@/components/ui'
import { UserResponse, UserCreate, UserUpdate, UserRole, AdminPasswordReset } from '@/generated'
import { useLanguage } from '@/contexts/LanguageContext'

interface UserManagementProps {
  onClose: () => void
}

export default function UserManagement({ onClose }: UserManagementProps) {
  const { t } = useLanguage()
  const { user } = useAuth()
  const [users, setUsers] = useState<UserResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [createLoading, setCreateLoading] = useState(false)
  const [createForm, setCreateForm] = useState({
    username: '',
    email: '',
    fullName: '',
    password: '',
    userRole: 'user' as UserRole
  })
  const [editingUser, setEditingUser] = useState<UserResponse | null>(null)
  const [editForm, setEditForm] = useState({
    username: '',
    email: '',
    fullName: '',
    userRole: 'user' as UserRole
  })
  const [editLoading, setEditLoading] = useState(false)
  const [showPasswordSection, setShowPasswordSection] = useState(false)
  const [passwordForm, setPasswordForm] = useState({
    newPassword: '',
    confirmPassword: ''
  })

  useEffect(() => {
    if (user?.user_role === 'admin') {
      loadUsers()
    }
  }, [user])

  const loadUsers = async (skip: number = 0, limit: number = 100) => {
    try {
      setLoading(true)
      const response = await authApi.getAllUsersApiAuthUsersGet({ skip, limit })
      setUsers(response || [])
    } catch (error) {
      console.error('Error loading users:', error)
      alert(t('userManagement.loadError'))
    } finally {
      setLoading(false)
    }
  }

  const handleCreateUser = async () => {
    try {
      setCreateLoading(true)
      
      // Validate password length
      if (createForm.password.length < 8) {
        alert(t('userManagement.passwordMinLength'))
        return
      }
      
      const userData: UserCreate = {
        username: createForm.username,
        email: createForm.email,
        fullName: createForm.fullName,
        password: createForm.password,
        userRole: createForm.userRole
      }

      await authApi.createUserApiAuthUsersPost({
        userCreate: userData
      })

      // Reset form and reload users
      setCreateForm({
        username: '',
        email: '',
        fullName: '',
        password: '',
        userRole: 'user'
      })
      setShowCreateForm(false)
      loadUsers()
    } catch (error: any) {
      console.error('Error creating user:', error)
      const errorMessage = error?.response?.data?.detail || t('userManagement.createError')
      alert(errorMessage)
    } finally {
      setCreateLoading(false)
    }
  }

  const handleEditUser = (userItem: UserResponse) => {
    setEditingUser(userItem)
    setEditForm({
      username: userItem.username,
      email: userItem.email,
      fullName: userItem.fullName,
      userRole: userItem.userRole
    })
    setShowPasswordSection(false)
    setPasswordForm({ newPassword: '', confirmPassword: '' })
  }

  const handleUpdateUser = async () => {
    if (!editingUser) return

    try {
      setEditLoading(true)
      
      const updateData: UserUpdate = {
        fullName: editForm.fullName,
        email: editForm.email,
        userRole: editForm.userRole
      }

      await authApi.updateUserApiAuthUsersUserIdPut({
        userId: editingUser.id,
        userUpdate: updateData
      })

      setEditingUser(null)
      loadUsers()
    } catch (error: any) {
      console.error('Error updating user:', error)
      const errorMessage = error?.response?.data?.detail || t('userManagement.updateError')
      alert(errorMessage)
    } finally {
      setEditLoading(false)
    }
  }

  const handleChangePassword = async () => {
    if (!editingUser) return

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      alert(t('userManagement.passwordsDoNotMatch'))
      return
    }

    if (passwordForm.newPassword.length < 8) {
      alert(t('userManagement.passwordMinLength'))
      return
    }

    try {
      setEditLoading(true)
      
      const resetData: AdminPasswordReset = {
        newPassword: passwordForm.newPassword
      }

      await authApi.adminResetPasswordApiAuthUsersUserIdResetPasswordPost({
        userId: editingUser.id,
        adminPasswordReset: resetData
      })

      setShowPasswordSection(false)
      setPasswordForm({ newPassword: '', confirmPassword: '' })
      alert(t('userManagement.passwordResetSuccess'))
    } catch (error: any) {
      console.error('Error resetting password:', error)
      const errorMessage = error?.response?.data?.detail || t('userManagement.resetPasswordError')
      alert(errorMessage)
    } finally {
      setEditLoading(false)
    }
  }

  const handleDeleteUser = async () => {
    if (!editingUser) return
    if (!confirm(t('userManagement.confirmDelete'))) return

    try {
      await authApi.deleteUserApiAuthUsersUserIdDelete({ userId: editingUser.id })
      setEditingUser(null)
      loadUsers()
    } catch (error: any) {
      console.error('Error deleting user:', error)
      const errorMessage = error?.response?.data?.detail || t('userManagement.deleteError')
      alert(errorMessage)
    }
  }

  if (user?.user_role !== 'admin') {
    return null
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">{t('userManagement.title')}</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>

          <div className="flex justify-between items-center mb-4">
            <p className="text-gray-600">{t('userManagement.description')}</p>
            <Button
              onClick={() => setShowCreateForm(true)}
            >
              {t('userManagement.createNewUser')}
            </Button>
          </div>

          {showCreateForm && (
            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <h3 className="text-lg font-semibold mb-3">{t('userManagement.createNewUser')}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('userManagement.username')}
                  </label>
                  <input
                    type="text"
                    value={createForm.username}
                    onChange={(e) => setCreateForm({ ...createForm, username: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('userManagement.email')}
                  </label>
                  <input
                    type="email"
                    value={createForm.email}
                    onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('userManagement.fullName')}
                  </label>
                  <input
                    type="text"
                    value={createForm.fullName}
                    onChange={(e) => setCreateForm({ ...createForm, fullName: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('userManagement.password')}
                  </label>
                  <input
                    type="password"
                    value={createForm.password}
                    onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('userManagement.role')}
                  </label>
                  <select
                    value={createForm.userRole}
                    onChange={(e) => setCreateForm({ ...createForm, userRole: e.target.value as UserRole })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
                  >
                    <option value="user">{t('userManagement.user')}</option>
                    <option value="admin">{t('userManagement.admin')}</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-4">
                <Button
                  onClick={() => setShowCreateForm(false)}
                  variant="secondary"
                >
                  {t('userManagement.cancel')}
                </Button>
                <Button
                  onClick={handleCreateUser}
                  disabled={createLoading}
                >
                  {createLoading ? t('userManagement.creating') : t('userManagement.createUser')}
                </Button>
              </div>
            </div>
          )}

          {loading ? (
            <div className="text-center py-8">
              <div className="text-lg">{t('userManagement.loading')}</div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('userManagement.username')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('userManagement.email')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('userManagement.fullName')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('userManagement.role')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('documentManagement.actions')}
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {users.map((userItem) => (
                    <tr key={userItem.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {userItem.username}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {userItem.email}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {userItem.fullName}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          userItem.userRole === 'admin' 
                            ? 'bg-red-100 text-red-800' 
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {userItem.userRole}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <button
                          onClick={() => handleEditUser(userItem)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          {t('userManagement.edit')}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Edit User Modal */}
      {editingUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-900">{t('userManagement.editUser')}</h3>
                <button
                  onClick={() => setEditingUser(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('userManagement.username')}
                  </label>
                  <input
                    type="text"
                    value={editForm.username}
                    disabled
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">{t('userManagement.usernameCannotChange')}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('userManagement.email')}
                  </label>
                  <input
                    type="email"
                    value={editForm.email}
                    onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('userManagement.fullName')}
                  </label>
                  <input
                    type="text"
                    value={editForm.fullName}
                    onChange={(e) => setEditForm({ ...editForm, fullName: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('userManagement.role')}
                  </label>
                  {editingUser.id === user?.id ? (
                    <input
                      type="text"
                      value={editForm.userRole}
                      disabled
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-500"
                    />
                  ) : (
                    <select
                      value={editForm.userRole}
                      onChange={(e) => setEditForm({ ...editForm, userRole: e.target.value as UserRole })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
                    >
                      <option value="user">{t('userManagement.user')}</option>
                      <option value="admin">{t('userManagement.admin')}</option>
                    </select>
                  )}
                </div>

                {/* Password Section */}
                <div className="border-t pt-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-medium text-gray-700">{t('userManagement.resetPassword')}</h4>
                    <button
                      type="button"
                      onClick={() => setShowPasswordSection(!showPasswordSection)}
                      className="text-sm text-violet-600 hover:text-violet-800"
                    >
                      {showPasswordSection ? t('userManagement.cancel') : t('userManagement.resetPassword')}
                    </button>
                  </div>

                  {showPasswordSection && (
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-600 mb-1">
                          {t('userManagement.newPassword')}
                        </label>
                        <input
                          type="password"
                          value={passwordForm.newPassword}
                          onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
                          placeholder={t('userManagement.enterNewPassword')}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-600 mb-1">
                          {t('userManagement.confirmPassword')}
                        </label>
                        <input
                          type="password"
                          value={passwordForm.confirmPassword}
                          onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
                          placeholder={t('userManagement.confirmNewPassword')}
                        />
                      </div>
                      <div className="flex justify-end">
                        <Button
                          onClick={handleChangePassword}
                          disabled={editLoading || !passwordForm.newPassword || !passwordForm.confirmPassword}
                          className="bg-green-600 hover:bg-green-700 text-white"
                        >
                          {editLoading ? t('userManagement.resetting') : t('userManagement.resetPassword')}
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex justify-between mt-6">
                <div>
                  {editingUser.id !== user?.id && (
                    <Button
                      onClick={handleDeleteUser}
                      variant="secondary"
                      className="bg-red-600 hover:bg-red-700 text-white"
                    >
                      {t('userManagement.deleteUser')}
                    </Button>
                  )}
                </div>
                <div className="flex space-x-3">
                  <Button
                    onClick={() => setEditingUser(null)}
                    variant="secondary"
                    disabled={editLoading}
                  >
                    {t('userManagement.cancel')}
                  </Button>
                  <Button
                    onClick={handleUpdateUser}
                    disabled={editLoading}
                  >
                    {editLoading ? t('userManagement.saving') : t('userManagement.saveChanges')}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
