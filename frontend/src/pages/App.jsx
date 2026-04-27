import { UploadScreen } from './UploadScreen'
import { TradeReviewScreen } from './TradeReviewScreen'
import { PositionsScreen } from './PositionsScreen'
import { ReportsScreen } from './ReportsScreen'

export function App() {
  return (
    <main style={{ fontFamily: 'sans-serif', maxWidth: 960, margin: '0 auto' }}>
      <h1>IRPF SINACOR (BTG)</h1>
      <UploadScreen />
      <TradeReviewScreen />
      <PositionsScreen />
      <ReportsScreen />
    </main>
  )
}
