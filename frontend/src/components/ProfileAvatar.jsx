import React from 'react';

/**
 * Renders a profile photo if provided, else a coral-circle with the user's
 * first initial. Used everywhere a profile picture appears so users without
 * an uploaded photo still get a consistent placeholder.
 */
export default function ProfileAvatar({
  photo,
  firstName = '',
  size = 96,
  className = '',
  alt,
}) {
  const initial = (firstName || '?').trim().charAt(0).toUpperCase();
  const dimensions = { width: size, height: size, fontSize: Math.round(size * 0.42) };

  if (photo) {
    return (
      <img
        src={photo}
        alt={alt || firstName}
        className={`rounded-full object-cover ${className}`}
        style={dimensions}
      />
    );
  }

  return (
    <div
      className={`rounded-full bg-gradient-to-br from-[#E76F51] to-[#E9C46A] flex items-center justify-center text-white font-bold ${className}`}
      style={dimensions}
      aria-label={alt || `${firstName || 'User'} avatar`}
    >
      {initial}
    </div>
  );
}
