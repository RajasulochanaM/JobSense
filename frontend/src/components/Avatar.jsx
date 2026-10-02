import { initials } from '../utils/format';

/** Profile picture when one is uploaded, otherwise an initials avatar in the chosen colour. */
export default function Avatar({ user, size = 34, className = '' }) {
  const style = { width: size, height: size, fontSize: Math.round(size * 0.4) };
  if (user?.avatar_image) {
    return <img src={user.avatar_image} alt="" className={`avatar avatar-img ${className}`} style={style} />;
  }
  return (
    <span className={`avatar avatar-${user?.avatar_color || 'burgundy'} ${className}`} style={style} aria-hidden="true">
      {initials(user?.name)}
    </span>
  );
}
