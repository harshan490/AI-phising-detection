import React from 'react';

const DotSpectrumBackground = () => {
  return (
    <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none bg-background">
      {/* Background gradients */}
      <div className="absolute inset-0 bg-background/80 mix-blend-multiply z-10 backdrop-blur-[50px]"></div>
      
      {/* Animated rolling PS text built from dots effect */}
      <div className="absolute inset-[-50%] animate-roll opacity-[0.03]" style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='400' height='200' viewBox='0 0 400 200' xmlns='http://www.w3.org/2000/svg'%3E%3Ctext x='50%25' y='50%25' font-family='sans-serif' font-weight='900' font-size='160' fill='rgba(255,255,255,1)' text-anchor='middle' dominant-baseline='middle' letter-spacing='-5'%3EPS%3C/text%3E%3C/svg%3E")`,
        backgroundSize: '400px 200px',
        backgroundRepeat: 'repeat',
        maskImage: 'radial-gradient(circle at center, black 40%, transparent 80%)',
        WebkitMaskImage: 'radial-gradient(circle at center, black 40%, transparent 80%)',
      }}>
        {/* We overlay a dot pattern to make it a "dot spectrum" */}
        <div className="absolute inset-0" style={{
            backgroundImage: 'radial-gradient(rgba(0,0,0,1) 2px, transparent 2.5px)',
            backgroundSize: '8px 8px',
        }}></div>
      </div>
      
      {/* Ambient glass orbs */}
      <div className="absolute top-[20%] left-[20%] w-[40vw] h-[40vw] max-w-[600px] max-h-[600px] bg-primary/20 rounded-full blur-[120px] animate-float opacity-50 mix-blend-screen"></div>
      <div className="absolute bottom-[20%] right-[20%] w-[35vw] h-[35vw] max-w-[500px] max-h-[500px] bg-secondary/20 rounded-full blur-[100px] animate-float opacity-40 mix-blend-screen" style={{ animationDelay: '2s' }}></div>
    </div>
  );
};

export default DotSpectrumBackground;
