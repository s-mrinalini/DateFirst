import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import axios from 'axios';
import { 
  Camera, ArrowLeft, Upload, CheckCircle, AlertCircle, RefreshCw
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { useAuth } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const GESTURES = [
  { id: 'thumbs_up', label: 'Thumbs Up', emoji: '👍', instruction: 'Give a thumbs up with your right hand' },
  { id: 'peace', label: 'Peace Sign', emoji: '✌️', instruction: 'Make a peace sign with your left hand' },
  { id: 'wave', label: 'Wave', emoji: '👋', instruction: 'Wave at the camera' },
  { id: 'point', label: 'Point Up', emoji: '☝️', instruction: 'Point up with your index finger' },
];

export default function PhotoVerificationPage() {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const fileInputRef = useRef(null);
  
  const [step, setStep] = useState('intro'); // intro, capture, uploading, submitted
  const [gesture, setGesture] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Randomly select a gesture when moving to capture step
  const startVerification = () => {
    const randomGesture = GESTURES[Math.floor(Math.random() * GESTURES.length)];
    setGesture(randomGesture);
    setStep('capture');
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('Image must be less than 10MB');
      return;
    }

    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleUpload = async () => {
    if (!selectedFile || !gesture) return;

    setUploading(true);
    setStep('uploading');
    
    try {
      // Create form data
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('gesture_type', gesture.id);

      // Simulate progress for UX
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await axios.post(`${API}/verification/photo/submit`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      toast.success('Photo submitted for verification!');
      setStep('submitted');
      
      // Refresh user data
      setTimeout(() => {
        refreshUser();
      }, 1000);

    } catch (error) {
      console.error('Upload error:', error);
      toast.error(error.response?.data?.detail || 'Failed to upload photo');
      setStep('capture');
      setUploadProgress(0);
    } finally {
      setUploading(false);
    }
  };

  const resetVerification = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setUploadProgress(0);
    setGesture(null);
    setStep('intro');
  };

  return (
    <div className="min-h-screen bg-[#FDFCF8] pb-24">
      {/* Header */}
      <div className="bg-white border-b border-stone-200 sticky top-0 z-10">
        <div className="max-w-lg mx-auto px-4 py-4 flex items-center gap-3">
          <button 
            onClick={() => navigate(-1)} 
            className="p-2 hover:bg-stone-100 rounded-full"
            data-testid="back-btn"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <Camera className="w-6 h-6 text-[#E76F51]" />
            <h1 className="text-xl font-bold" style={{ fontFamily: 'Syne, sans-serif' }}>
              Photo Verification
            </h1>
          </div>
        </div>
      </div>

      <div className="max-w-lg mx-auto px-4 py-6">
        {/* Step: Intro */}
        {step === 'intro' && (
          <div className="space-y-6">
            <Card className="border-[#2A9D8F]/20 bg-[#2A9D8F]/5">
              <CardContent className="pt-6">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-full bg-[#2A9D8F]/20 flex items-center justify-center flex-shrink-0">
                    <CheckCircle className="w-6 h-6 text-[#2A9D8F]" />
                  </div>
                  <div>
                    <h2 className="font-bold text-lg mb-2" style={{ fontFamily: 'Syne, sans-serif' }}>
                      Why verify your photo?
                    </h2>
                    <ul className="text-sm text-[#57534E] space-y-2">
                      <li className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-[#2A9D8F] flex-shrink-0" /> 
                        Build trust with potential matches
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-[#2A9D8F] flex-shrink-0" /> 
                        Get a verified badge on your profile
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-[#2A9D8F] flex-shrink-0" /> 
                        Show you are a real person
                      </li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">How it works</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#E76F51]/10 flex items-center justify-center flex-shrink-0">
                    <span className="text-[#E76F51] font-bold">1</span>
                  </div>
                  <div>
                    <p className="font-medium">We will show you a gesture</p>
                    <p className="text-sm text-[#57534E]">You will need to pose with a specific gesture</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#E76F51]/10 flex items-center justify-center flex-shrink-0">
                    <span className="text-[#E76F51] font-bold">2</span>
                  </div>
                  <div>
                    <p className="font-medium">Take a selfie</p>
                    <p className="text-sm text-[#57534E]">Make sure your face is clearly visible</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#E76F51]/10 flex items-center justify-center flex-shrink-0">
                    <span className="text-[#E76F51] font-bold">3</span>
                  </div>
                  <div>
                    <p className="font-medium">We review it</p>
                    <p className="text-sm text-[#57534E]">Usually within 24 hours</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Button 
              onClick={startVerification}
              className="w-full rounded-full bg-[#E76F51] hover:bg-[#D65D40] py-6 text-lg"
              data-testid="start-verification-btn"
            >
              Start Verification
            </Button>
          </div>
        )}

        {/* Step: Capture */}
        {step === 'capture' && gesture && (
          <div className="space-y-6">
            <Card className="border-[#E9C46A] bg-[#E9C46A]/10">
              <CardContent className="pt-6 text-center">
                <div className="text-6xl mb-4">{gesture.emoji}</div>
                <h2 className="font-bold text-xl mb-2" style={{ fontFamily: 'Syne, sans-serif' }}>
                  {gesture.label}
                </h2>
                <p className="text-[#57534E]">{gesture.instruction}</p>
              </CardContent>
            </Card>

            {/* Preview Area */}
            <div 
              className="relative aspect-square bg-stone-100 rounded-2xl overflow-hidden cursor-pointer border-2 border-dashed border-stone-300 hover:border-[#E76F51] transition-colors"
              onClick={() => fileInputRef.current?.click()}
              data-testid="upload-area"
            >
              {previewUrl ? (
                <img 
                  src={previewUrl} 
                  alt="Preview" 
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-[#A8A29E]">
                  <Upload className="w-12 h-12 mb-4" />
                  <p className="font-medium">Tap to upload your selfie</p>
                  <p className="text-sm mt-1">JPG, PNG up to 10MB</p>
                </div>
              )}
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              capture="user"
              onChange={handleFileSelect}
              className="hidden"
              data-testid="file-input"
            />

            <div className="bg-stone-50 rounded-xl p-4">
              <h3 className="font-medium mb-2 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-[#E9C46A]" />
                Tips for a good photo
              </h3>
              <ul className="text-sm text-[#57534E] space-y-1">
                <li>• Good lighting on your face</li>
                <li>• Face clearly visible, no sunglasses</li>
                <li>• Show the gesture clearly</li>
                <li>• No filters or heavy editing</li>
              </ul>
            </div>

            <div className="flex gap-3">
              <Button 
                variant="outline"
                onClick={resetVerification}
                className="flex-1 rounded-full"
              >
                Cancel
              </Button>
              <Button 
                onClick={handleUpload}
                disabled={!selectedFile}
                className="flex-1 rounded-full bg-[#E76F51] hover:bg-[#D65D40]"
                data-testid="submit-btn"
              >
                Submit for Review
              </Button>
            </div>
          </div>
        )}

        {/* Step: Uploading */}
        {step === 'uploading' && (
          <div className="space-y-6 text-center py-12">
            <div className="w-20 h-20 mx-auto rounded-full bg-[#E76F51]/10 flex items-center justify-center">
              <RefreshCw className="w-10 h-10 text-[#E76F51] animate-spin" />
            </div>
            <div>
              <h2 className="font-bold text-xl mb-2" style={{ fontFamily: 'Syne, sans-serif' }}>
                Uploading...
              </h2>
              <p className="text-[#57534E]">Please wait while we process your photo</p>
            </div>
            
            {/* Progress Bar */}
            <div className="max-w-xs mx-auto">
              <div className="h-2 bg-stone-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-[#E76F51] transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-sm text-[#A8A29E] mt-2">{uploadProgress}%</p>
            </div>
          </div>
        )}

        {/* Step: Submitted */}
        {step === 'submitted' && (
          <div className="space-y-6 text-center py-12">
            <div className="w-20 h-20 mx-auto rounded-full bg-[#2A9D8F]/10 flex items-center justify-center">
              <CheckCircle className="w-10 h-10 text-[#2A9D8F]" />
            </div>
            <div>
              <h2 className="font-bold text-xl mb-2" style={{ fontFamily: 'Syne, sans-serif' }}>
                Photo Submitted!
              </h2>
              <p className="text-[#57534E]">
                Your verification photo is being reviewed.<br />
                We will notify you once it is approved.
              </p>
            </div>
            
            <Card className="text-left">
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">What happens next?</h3>
                <ul className="text-sm text-[#57534E] space-y-2">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-[#2A9D8F] flex-shrink-0 mt-0.5" />
                    Our team reviews your photo (usually within 24 hours)
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-[#2A9D8F] flex-shrink-0 mt-0.5" />
                    You will get a notification when approved
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-[#2A9D8F] flex-shrink-0 mt-0.5" />
                    Your verified badge will appear on your profile
                  </li>
                </ul>
              </CardContent>
            </Card>

            <Button 
              onClick={() => navigate('/safety')}
              className="w-full rounded-full bg-[#2A9D8F] hover:bg-[#238B7E]"
              data-testid="back-to-safety-btn"
            >
              Back to Safety Center
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
