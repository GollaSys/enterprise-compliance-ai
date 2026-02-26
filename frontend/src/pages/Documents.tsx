import React, { useState, useCallback } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { CloudUpload, Delete } from '@mui/icons-material';
import { DataGrid, GridColDef, GridActionsCellItem } from '@mui/x-data-grid';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useDropzone } from 'react-dropzone';
import { useSnackbar } from 'notistack';
import { documentsAPI } from '../services/api';

const Documents: React.FC = () => {
  const [uploadOpen, setUploadOpen] = useState(false);
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  const { data, isLoading, error } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentsAPI.list().then(res => res.data),
  });

  const deleteMutation = useMutation({
    mutationFn: (docId: string) => documentsAPI.delete(docId),
    onSuccess: () => {
      enqueueSnackbar('Document deleted', { variant: 'success' });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: () => {
      enqueueSnackbar('Failed to delete document', { variant: 'error' });
    },
  });

  const columns: GridColDef[] = [
    { field: 'filename', headerName: 'Document Name', flex: 1, minWidth: 200 },
    { field: 'doc_type', headerName: 'Type', width: 120 },
    { field: 'upload_date', headerName: 'Upload Date', width: 200 },
    { field: 'status', headerName: 'Status', width: 120 },
    {
      field: 'actions',
      type: 'actions',
      headerName: '',
      width: 60,
      getActions: (params) => [
        <GridActionsCellItem
          icon={<Delete />}
          label="Delete"
          onClick={() => deleteMutation.mutate(params.row.id)}
          sx={{ color: 'error.main' }}
        />,
      ],
    },
  ];

  const uploadMutation = useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return documentsAPI.upload(formData);
    },
    onSuccess: (res) => {
      enqueueSnackbar(`Document "${res.data.filename}" uploaded successfully`, { variant: 'success' });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setUploadOpen(false);
    },
    onError: () => {
      enqueueSnackbar('Failed to upload document', { variant: 'error' });
    },
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      uploadMutation.mutate(acceptedFiles[0]);
    }
  }, [uploadMutation]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/csv': ['.csv'],
    },
    maxFiles: 1,
  });

  const documents = data?.documents || [];
  const rows = documents.map((doc: any, idx: number) => ({ ...doc, id: doc.id || idx }));

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load documents. Please ensure the backend server is running.
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
            Document Management
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Upload and manage compliance documents
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<CloudUpload />} onClick={() => setUploadOpen(true)}>
          Upload Document
        </Button>
      </Box>

      <Card>
        <CardContent>
          <Box sx={{ height: 400, width: '100%' }}>
            {isLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                <CircularProgress />
              </Box>
            ) : (
              <DataGrid
                rows={rows}
                columns={columns}
                initialState={{
                  pagination: { paginationModel: { pageSize: 10, page: 0 } },
                  sorting: { sortModel: [{ field: 'upload_date', sort: 'desc' }] },
                }}
                pageSizeOptions={[10]}
                checkboxSelection
                disableRowSelectionOnClick
              />
            )}
          </Box>
        </CardContent>
      </Card>

      <Dialog open={uploadOpen} onClose={() => setUploadOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Upload Document</DialogTitle>
        <DialogContent>
          <Box
            {...getRootProps()}
            sx={{
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.400',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              bgcolor: isDragActive ? 'action.hover' : 'transparent',
              mt: 1,
            }}
          >
            <input {...getInputProps()} />
            {uploadMutation.isPending ? (
              <CircularProgress />
            ) : isDragActive ? (
              <Typography>Drop the file here...</Typography>
            ) : (
              <Box>
                <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                <Typography>Drag & drop a file here, or click to select</Typography>
                <Typography variant="caption" color="text.secondary">
                  Supported: PDF, DOC, DOCX, TXT, CSV
                </Typography>
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadOpen(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Documents;
