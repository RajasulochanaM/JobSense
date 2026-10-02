import { useCallback, useState } from 'react';
import { savedApi } from '../services/api';
import { useToast } from '../context/ToastContext';

/** Save / unsave a job and report the new state through `onChange(jobId, isSaved)`. */
export function useSaveJob(onChange) {
  const toast = useToast();
  const [pending, setPending] = useState(null);

  const toggle = useCallback(async (job) => {
    setPending(job.job_id);
    try {
      if (job.is_saved) {
        await savedApi.unsave(job.job_id);
        toast.info('Removed from saved jobs');
      } else {
        await savedApi.save(job.job_id);
        toast.success('Job saved');
      }
      onChange?.(job.job_id, !job.is_saved);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setPending(null);
    }
  }, [onChange, toast]);

  return { toggle, pending };
}
