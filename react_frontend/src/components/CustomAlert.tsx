import React, { useEffect } from 'react';
import Alert from '@mui/material/Alert';
import Stack from '@mui/material/Stack';
import Fade from '@mui/material/Fade';

interface CustomAlertProps {
  severity: 'error' | 'warning' | 'info' | 'success';
  message: string;
  open: boolean;
  onClose: () => void;
}


const CustomAlert: React.FC<CustomAlertProps> = ({ severity, message, open, onClose }): React.ReactElement | null => {
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    if (open) {
      timer = setTimeout(() => {
        onClose(); // Call the onClose function after n seconds
      }, 5000);
    }
    return () => clearTimeout(timer); // Clean up the timer
  }, [open, onClose]);
  // Tells React to re-run the effect in the useEffect hook only when the values of open or onClose change.

  if (!open) return null;

  return (
    <Stack sx={{ width: '100%' }} spacing={2}>
      <Fade in={open} timeout={500}>
        <Alert variant='filled' severity={severity} onClose={onClose}>
          {/* onClose function is passed to allow manual closing of the alert, complementing the automatic dismissal mechanism. */}
            {message}
        </Alert>
      </Fade>
    </Stack>
  );
};

export default CustomAlert;
