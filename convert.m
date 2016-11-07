genre_ids = [18 1153 100007 17 15 6 20 14 21];
for genre_id = genre_ids
    sprintf('starting genre_id = %d', genre_id)
    files = dir(sprintf('scraper\\clips\\%d\\*.mp3', genre_id));
    [num_files, ~] = size(files);
    sprintf('converting %d files', num_files);
    filenames = extractfield(files, 'name');
    X = zeros(num_files, 22*1020);
    y = ones(num_files, 1) * genre_id;
    for i = 1:num_files
        filename = char(filenames(i));
        sprintf('converting (%d/%d) %s', i, num_files, filename)
        cc = mp32mfcc(sprintf('scraper\\clips\\%d\\%s',genre_id, filename));
        X(i,:) = reshape(cc, 1, 22*1020);
    end
    sprintf('saving results')
    save(sprintf('%d', genre_id), 'X', 'y');
end