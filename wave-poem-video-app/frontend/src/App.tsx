import { useState, useEffect, useRef } from 'react'
import { Play, Repeat, Download, Loader2, CheckCircle, XCircle, Upload } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface PoemStats {
  available: number
  used: number
}

interface TaskStatus {
  task_id: string
  status: string
  current: number
  total: number
  videos: string[]
  message: string | null
}

interface VideoInfo {
  filename: string
  size: number
  created: string
}

function App() {
  const [poemStats, setPoemStats] = useState<PoemStats | null>(null)
  const [batchCount, setBatchCount] = useState<number>(1)
  const [currentTask, setCurrentTask] = useState<TaskStatus | null>(null)
  const [videos, setVideos] = useState<VideoInfo[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [uploadMessage, setUploadMessage] = useState<string>('')
  const poemInputRef = useRef<HTMLInputElement>(null)
  const imageInputRef = useRef<HTMLInputElement>(null)
  const bgmInputRef = useRef<HTMLInputElement>(null)

  const loadPoemStats = async () => {
    try {
      const response = await fetch(`${API_URL}/api/poems/available`)
      const data = await response.json()
      setPoemStats(data)
    } catch (error) {
      console.error('Failed to load poem stats:', error)
    }
  }

  const loadVideos = async () => {
    try {
      const response = await fetch(`${API_URL}/api/videos`)
      const data = await response.json()
      setVideos(data.videos)
    } catch (error) {
      console.error('Failed to load videos:', error)
    }
  }

  useEffect(() => {
    loadPoemStats()
    loadVideos()
  }, [])

  const pollTaskStatus = async (taskId: string) => {
    let attempts = 0
    const maxAttempts = 150 // 5 minutes max (150 * 2 seconds)
    
    const interval = setInterval(async () => {
      attempts++
      
      if (attempts > maxAttempts) {
        clearInterval(interval)
        setIsGenerating(false)
        setCurrentTask({
          task_id: taskId,
          status: 'error',
          current: 0,
          total: 1,
          videos: [],
          message: 'タイムアウト: 生成に時間がかかりすぎています。サーバーの容量不足の可能性があります。'
        })
        return
      }
      
      try {
        const response = await fetch(`${API_URL}/api/status/${taskId}`)
        
        if (!response.ok) {
          throw new Error('サーバーエラー')
        }
        
        const data: TaskStatus = await response.json()
        setCurrentTask(data)

        if (data.status === 'completed' || data.status === 'error') {
          clearInterval(interval)
          setIsGenerating(false)
          loadPoemStats()
          loadVideos()
        }
      } catch (error) {
        console.error('Failed to poll task status:', error)
        clearInterval(interval)
        setIsGenerating(false)
        setCurrentTask({
          task_id: taskId,
          status: 'error',
          current: 0,
          total: 1,
          videos: [],
          message: 'サーバーエラー: 生成中にエラーが発生しました。サーバーのメモリ不足の可能性があります。'
        })
      }
    }, 2000)
  }

  const handleSingleGenerate = async () => {
    setIsGenerating(true)
    setCurrentTask({
      task_id: '',
      status: 'processing',
      current: 0,
      total: 1,
      videos: [],
      message: '動画生成を開始しています...'
    })
    try {
      const response = await fetch(`${API_URL}/api/generate/single`, {
        method: 'POST',
      })
      const data = await response.json()
      pollTaskStatus(data.task_id)
    } catch (error) {
      console.error('Failed to start generation:', error)
      setIsGenerating(false)
      setCurrentTask({
        task_id: '',
        status: 'error',
        current: 0,
        total: 1,
        videos: [],
        message: '生成の開始に失敗しました'
      })
    }
  }

  const handleBatchGenerate = async () => {
    setIsGenerating(true)
    setCurrentTask({
      task_id: '',
      status: 'processing',
      current: 0,
      total: batchCount,
      videos: [],
      message: `${batchCount}個の動画生成を開始しています...`
    })
    try {
      const response = await fetch(`${API_URL}/api/generate/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ count: batchCount }),
      })
      const data = await response.json()
      pollTaskStatus(data.task_id)
    } catch (error) {
      console.error('Failed to start generation:', error)
      setIsGenerating(false)
      setCurrentTask({
        task_id: '',
        status: 'error',
        current: 0,
        total: batchCount,
        videos: [],
        message: '生成の開始に失敗しました'
      })
    }
  }

  const handleDownload = (filename: string) => {
    window.open(`${API_URL}/api/videos/${filename}`, '_blank')
  }

  const handleFileUpload = async (file: File, endpoint: string, fileType: string) => {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${API_URL}/api/upload/${endpoint}`, {
        method: 'POST',
        body: formData,
      })
      
      if (response.ok) {
        setUploadMessage(`${fileType}をアップロードしました: ${file.name}`)
        loadPoemStats()
        setTimeout(() => setUploadMessage(''), 3000)
      } else {
        const error = await response.json()
        setUploadMessage(`エラー: ${error.detail}`)
      }
    } catch (error) {
      setUploadMessage(`アップロードに失敗しました`)
    }
  }

  const handlePoemUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFileUpload(file, 'poem', '詩ファイル')
  }

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFileUpload(file, 'image', '画像')
  }

  const handleBgmUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFileUpload(file, 'bgm', 'BGM')
  }

  const progress = currentTask
    ? (currentTask.current / currentTask.total) * 100
    : 0

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            無条件の波動
          </h1>
          <p className="text-lg text-gray-600">
            詩の自動動画生成システム
          </p>
        </div>

        {isGenerating && currentTask && (
          <Card className="mb-6 border-blue-500 border-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
                動画生成中...
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">
                      進捗: {currentTask.current} / {currentTask.total}
                    </span>
                    <span className="text-sm font-medium text-blue-600">
                      {progress.toFixed(0)}%
                    </span>
                  </div>
                  <Progress value={progress} className="h-3" />
                </div>
                {currentTask.message && (
                  <Alert>
                    <AlertDescription className="font-medium">{currentTask.message}</AlertDescription>
                  </Alert>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="w-5 h-5" />
              ファイルアップロード
            </CardTitle>
            <CardDescription>
              詩ファイル、背景画像、BGMをアップロードしてください
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label htmlFor="poem-upload">詩ファイル (.txt)</Label>
                <input
                  ref={poemInputRef}
                  id="poem-upload"
                  type="file"
                  accept=".txt"
                  onChange={handlePoemUpload}
                  className="hidden"
                />
                <Button
                  onClick={() => poemInputRef.current?.click()}
                  variant="outline"
                  className="w-full mt-2"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  詩を選択
                </Button>
              </div>
              <div>
                <Label htmlFor="image-upload">背景画像 (9:16)</Label>
                <input
                  ref={imageInputRef}
                  id="image-upload"
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                />
                <Button
                  onClick={() => imageInputRef.current?.click()}
                  variant="outline"
                  className="w-full mt-2"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  画像を選択
                </Button>
              </div>
              <div>
                <Label htmlFor="bgm-upload">BGM (.mp3)</Label>
                <input
                  ref={bgmInputRef}
                  id="bgm-upload"
                  type="file"
                  accept=".mp3,audio/mpeg"
                  onChange={handleBgmUpload}
                  className="hidden"
                />
                <Button
                  onClick={() => bgmInputRef.current?.click()}
                  variant="outline"
                  className="w-full mt-2"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  BGMを選択
                </Button>
              </div>
            </div>
            {uploadMessage && (
              <Alert className="mt-4">
                <AlertDescription>{uploadMessage}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {poemStats && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>詩の統計</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <p className="text-2xl font-bold text-green-700">
                    {poemStats.available}
                  </p>
                  <p className="text-sm text-gray-600">利用可能</p>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <p className="text-2xl font-bold text-blue-700">
                    {poemStats.used}
                  </p>
                  <p className="text-sm text-gray-600">使用済み</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Play className="w-5 h-5" />
                単一生成
              </CardTitle>
              <CardDescription>
                1つの詩から動画を生成します
              </CardDescription>
            </CardHeader>
            <CardFooter>
              <Button
                onClick={handleSingleGenerate}
                disabled={isGenerating || !poemStats || poemStats.available === 0}
                className="w-full"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    生成中...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    生成開始
                  </>
                )}
              </Button>
            </CardFooter>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Repeat className="w-5 h-5" />
                バッチ生成
              </CardTitle>
              <CardDescription>
                複数の詩から動画を一度に生成します
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label htmlFor="batch-count">生成数</Label>
                <Input
                  id="batch-count"
                  type="number"
                  min={1}
                  max={poemStats?.available || 100}
                  value={batchCount}
                  onChange={(e) => setBatchCount(parseInt(e.target.value) || 1)}
                  disabled={isGenerating}
                />
              </div>
            </CardContent>
            <CardFooter>
              <Button
                onClick={handleBatchGenerate}
                disabled={isGenerating || !poemStats || poemStats.available === 0}
                className="w-full"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    生成中...
                  </>
                ) : (
                  <>
                    <Repeat className="w-4 h-4 mr-2" />
                    バッチ生成開始
                  </>
                )}
              </Button>
            </CardFooter>
          </Card>
        </div>

        {currentTask && !isGenerating && (
          <Card className={`mb-6 ${currentTask.status === 'completed' ? 'border-green-500 border-2' : currentTask.status === 'error' ? 'border-red-500 border-2' : ''}`}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {currentTask.status === 'completed' && (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                )}
                {currentTask.status === 'error' && (
                  <XCircle className="w-5 h-5 text-red-500" />
                )}
                {currentTask.status === 'completed' ? '生成完了' : 'エラー'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {currentTask.status === 'completed' && (
                  <Alert className="bg-green-50">
                    <AlertDescription className="font-medium text-green-800">
                      {currentTask.total}個の動画の生成が完了しました！下の「生成済み動画」セクションからダウンロードできます。
                    </AlertDescription>
                  </Alert>
                )}
                {currentTask.status === 'error' && currentTask.message && (
                  <Alert className="bg-red-50">
                    <AlertDescription className="font-medium text-red-800">
                      {currentTask.message}
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="w-5 h-5" />
              生成済み動画
            </CardTitle>
            <CardDescription>
              {videos.length}個の動画が利用可能です
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {videos.length === 0 ? (
                <p className="text-center text-gray-500 py-8">
                  まだ動画が生成されていません
                </p>
              ) : (
                videos.map((video) => (
                  <div
                    key={video.filename}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                  >
                    <div>
                      <p className="font-medium">{decodeURIComponent(video.filename)}</p>
                      <p className="text-sm text-gray-500">
                        {(video.size / 1024 / 1024).toFixed(2)} MB • {new Date(video.created).toLocaleString('ja-JP')}
                      </p>
                    </div>
                    <Button
                      onClick={() => handleDownload(video.filename)}
                      variant="outline"
                      size="sm"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      ダウンロード
                    </Button>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default App
