'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { authApi } from '@/api'
import { Button } from '@/components/ui'
import { UserResponse, UserUpdate, UserChangePassword } from '@/generated'

interface UserProfileProps {
  onClose: () => void
}

export default function UserProfile({ onClose }: UserProfileProps) {
  const { user, logout } = useAuth()
  const [isEditing, setIsEditing] = useState(false)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    fullName: ''
  })
  const [showPasswordSection, setShowPasswordSection] = useState(false)
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  })

  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username,
        email: user.email,
        fullName: user.full_name
      })
    }
  }, [user])

  const handleSave = async () => {
    if (!user) return

    try {
      setLoading(true)
      
      const updateData: UserUpdate = {
        email: formData.email,
        fullName: formData.fullName
      }

      await authApi.updateUserApiAuthUsersUserIdPut({
        userId: user.id,
        userUpdate: updateData
      })

      setIsEditing(false)
      // Refresh user data
      window.location.reload()
    } catch (error) {
      console.error('Error updating profile:', error)
      alert('Failed to update profile. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleChangePassword = async () => {
    if (!user) return

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      alert('New passwords do not match')
      return
    }

    if (passwordData.newPassword.length < 8) {
      alert('New password must be at least 8 characters long')
      return
    }

    try {
      setLoading(true)
      
      const passwordChangeData: UserChangePassword = {
        currentPassword: passwordData.currentPassword,
        newPassword: passwordData.newPassword
      }

      await authApi.changePasswordApiAuthChangePasswordPost({
        userChangePassword: passwordChangeData
      })

      setShowPasswordSection(false)
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' })
      alert('Password changed successfully. You will be logged out and need to log in again.')
      
      // Log out the user since their session is now invalid
      setTimeout(() => {
        logout()
      }, 2000)
    } catch (error: any) {
      console.error('Error changing password:', error)
      const errorMessage = error?.response?.data?.detail || 'Failed to change password'
      alert(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    if (user) {
      setFormData({
        username: user.username,
        email: user.email,
        fullName: user.full_name
      })
    }
    setIsEditing(false)
  }

  if (!user) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">User Profile</h2>
            <button
              onClick={onClose}
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
                Username
              </label>
              <div className="px-3 py-2 bg-gray-100 rounded-md text-gray-500">
                {user.username}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              {isEditing ? (
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              ) : (
                <p className="text-gray-900">{user.email}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Full Name
              </label>
              {isEditing ? (
                <input
                  type="text"
                  value={formData.fullName}
                  onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              ) : (
                <p className="text-gray-900">{user.full_name}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Role
              </label>
              <p className="text-gray-900 capitalize">{user.user_role}</p>
            </div>

            {/* Password Change Section */}
            <div className="border-t pt-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-medium text-gray-700">Change Password</h4>
                <button
                  type="button"
                  onClick={() => setShowPasswordSection(!showPasswordSection)}
                  className="text-sm text-violet-600 hover:text-violet-800"
                >
                  {showPasswordSection ? 'Cancel' : 'Change Password'}
                </button>
              </div>

              {showPasswordSection && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-600 mb-1">
                      Current Password
                    </label>
                    <input
                      type="password"
                      value={passwordData.currentPassword}
                      onChange={(e) => setPasswordData({ ...passwordData, currentPassword: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
                      placeholder="Enter current password"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-600 mb-1">
                      New Password
                    </label>
                    <input
                      type="password"
                      value={passwordData.newPassword}
                      onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
                      placeholder="Enter new password (min 8 characters)"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-600 mb-1">
                      Confirm New Password
                    </label>
                    <input
                      type="password"
                      value={passwordData.confirmPassword}
                      onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
                      placeholder="Confirm new password"
                    />
                  </div>
                  <div className="flex justify-end">
                    <Button
                      onClick={handleChangePassword}
                      disabled={loading || !passwordData.currentPassword || !passwordData.newPassword || !passwordData.confirmPassword}
                      className="bg-green-600 hover:bg-green-700 text-white"
                    >
                      {loading ? 'Changing...' : 'Change Password'}
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="flex justify-end space-x-3 mt-6">
            {isEditing ? (
              <>
                <Button
                  onClick={handleCancel}
                  variant="secondary"
                  disabled={loading}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={loading}
                >
                  {loading ? 'Saving...' : 'Save'}
                </Button>
              </>
            ) : (
              <Button
                onClick={() => setIsEditing(true)}
              >
                Edit Profile
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
