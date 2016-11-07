function CC = mp32mfcc(filename)
    [speech,fs] = audioread(filename); %insert song here
    length = 273000; %length of sample in ms
    Tw = length/510;
    Ts = Tw*.5;
    alpha = .95;
    M = 22;
    L = 22;
    window = blackmanharris(32);
    R = [22 22000];
    N = 22;
    speech = (speech(:,1)+speech(:,2))/2; %convert from stereo to audio
    [CC,~,~] =mfcc(speech,fs,Tw,Ts,alpha,window,R,M,N,L);
end

