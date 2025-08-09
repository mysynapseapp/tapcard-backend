try {
      const token = await AsyncStorage.getItem('token');
      const response = await fetch(`${API_URL}/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          username: profile.username,
          bio: profile.bio,
          dob: profile.dob,
        }),
      });

      if (response.ok) {
        Alert.alert('Success', 'Profile updated successfully');
        navigation.goBack();
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to update profile');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to save profile');
    }
  };
=======
  const handleSave = async () => {
    try {
      const token = await AsyncStorage.getItem('token');
      
      // Prepare the payload
      const payload = {
        username: profile.username,
        bio: profile.bio,
      };
      
      // Only include dob if it's valid
      if (profile.dob) {
        payload.dob = profile.dob;
      }

      const response = await fetch(`${API_URL}/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        Alert.alert('Success', 'Profile updated successfully');
        navigation.goBack();
      } else {
        const error = await response.json();
        console.error('Profile update error:', error);
        Alert.alert('Error', error.detail || 'Failed to update profile');
      }
    } catch (error) {
      console.error('Profile save error:', error);
      Alert.alert('Error', 'Failed to save profile');
    }
  };
